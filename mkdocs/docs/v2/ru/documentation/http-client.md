---
description: "Explains Kora HTTP clients, the OkHttp, Apache HttpClient and JDK transports, declarative client annotations, request and response mapping, interceptors, authorization and telemetry. Use when working with @HttpClient, @HttpRoute, @Path, @Query, @Header, @Cookie, @Json, @Mapping, @ResponseCodeMapper, @InterceptWith."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora HTTP clients, the OkHttp / Apache HttpClient / JDK transports, declarative client annotations, request and response mapping, interceptors, authorization and telemetry; key triggers include @HttpClient, @HttpRoute, @Path, @Query, @Header, @Cookie, @Json, @Mapping, @ResponseCodeMapper, @InterceptWith, HttpClientResponseMapper, HttpClientRequestMapper, HttpClientParameterWriter, HttpClientInterceptor, HttpClientModule, OkHttpClientModule, ApacheHttpClientModule, JdkHttpClientModule."
---

Модуль `HTTP-клиента` описывает исходящие HTTP-вызовы приложения: реализацию транспорта, преобразование запроса,
преобразование ответа, телеметрию и перехватчики. В Kora типизированные клиенты описываются декларативно через `@HttpClient`
и `@HttpRoute`, либо используется общий интерфейс `HttpClient` напрямую, когда запрос нужно собрать в коде.

Декларативный подход подходит для большинства интеграций с внешними службами: контракт метода становится контрактом удаленного вызова,
а Kora во время компиляции создает реализацию без использования `Reflection` во время работы. Императивный подход полезен для низкоуровневых
или динамических сценариев, где путь, заголовки, параметры или тело запроса удобнее собирать вручную.

Все вызовы HTTP-клиента в Kora **синхронные и блокирующие**: `HttpClient.execute()` возвращает `HttpClientResponse` напрямую,
а декларативный метод сразу возвращает результат. Параллелизм обеспечивается виртуальными потоками,
а не реактивными или корутинными типами возврата.

???+ tip "Совет"

    **Мы советуем** использовать подход, при котором первичен контракт в формате `OpenAPI`,
    а клиенты создаются с помощью генератора.
    Такой подход помогает сохранить согласованность контракта между потребителем и владельцем контракта
    и быстрее обновлять клиент при изменении контракта за счет замены файла описания.
    Подробнее про генератор смотрите в [разделе про генерацию из OpenAPI](openapi-codegen.md).

Если нужен пошаговый разбор перед справочным описанием, смотрите [HTTP-клиент](../guides/http-client.md) и [продвинутый HTTP-клиент](../guides/http-client-advanced.md).

## OkHttp { #okhttp }

Реализация `HTTP`-клиента на базе библиотеки [OkHttp](https://github.com/square/okhttp).
Сам модуль Kora написан на Java, но библиотека OkHttp написана на Kotlin и тянет собственные зависимости.
Этот транспорт стоит выбирать, если нужны `HTTP/2` или `HTTP/3`, сжатие `GZip` либо иные специфичные для OkHttp настройки.

### Подключение { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "io.koraframework:http-client-ok"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends OkHttpClientModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("io.koraframework:http-client-ok")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : OkHttpClientModule
    ```

Реализацией интерфейса `HttpClient` выступает `OkHttpClient` из пакета `io.koraframework.http.client.ok`.

### Конфигурация { #configuration }

Основные параметры конфигурации клиента OkHttp:

===! ":material-code-json: `Hocon`"

    ```javascript
    httpClient {
        connectTimeout = "5s" //(1)!
        readTimeout = "2m" //(2)!
    }
    ```

    1.  Максимальное время установки соединения (по умолчанию: `5s`)
    2.  Максимальное время чтения ответа (по умолчанию: `2m`)

=== ":simple-yaml: `YAML`"

    ```yaml
    httpClient:
      connectTimeout: "5s" #(1)!
      readTimeout: "2m" #(2)!
    ```

    1.  Максимальное время установки соединения (по умолчанию: `5s`)
    2.  Максимальное время чтения ответа (по умолчанию: `2m`)

??? note "Полная конфигурация"

    Пример полной конфигурации, описанной в классах `OkHttpClientConfig`
    и `HttpClientConfig` (указаны значения по умолчанию либо примерные значения):

    ===! ":material-code-json: `Hocon`"

        ```javascript
        httpClient {
            ok {
                followRedirects = true //(1)!
                retryOnConnectionFailure = true //(2)!
                httpVersion = "HTTP_1_1" //(3)!
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
        }
        ```

        1. Следовать ли [HTTP-перенаправлениям](https://developer.mozilla.org/ru/docs/Web/HTTP/Redirections) (по умолчанию: `true`)
        2. Повторять ли запрос после сбоя соединения; это может влиять на максимальное время установки соединения (по умолчанию: `true`)
        3. Максимальная используемая версия протокола `HTTP`, доступные значения: `HTTP_1_1` / `HTTP_2` / `HTTP_3` (по умолчанию: `HTTP_1_1`)
        4. Максимальное время установки соединения (по умолчанию: `5s`)
        5. Максимальное время чтения ответа (по умолчанию: `2m`)
        6. Использовать ли переменные окружения `https_proxy` / `HTTPS_PROXY` / `http_proxy` / `HTTP_PROXY` и `no_proxy` / `NO_PROXY` для настройки прокси (по умолчанию: `false`)
        7. Хост прокси-сервера (обязательный, если секция `proxy` присутствует, без значения по умолчанию)
        8. Порт прокси-сервера (обязательный, если секция `proxy` присутствует, без значения по умолчанию)
        9. Пользователь прокси-сервера (опционально, без значения по умолчанию)
        10. Пароль прокси-сервера (опционально, без значения по умолчанию)
        11. Хосты, которые исключаются из проксирования (опционально, без значения по умолчанию)

    === ":simple-yaml: `YAML`"

        ```yaml
        httpClient:
          ok:
            followRedirects: true #(1)!
            retryOnConnectionFailure: true #(2)!
            httpVersion: "HTTP_1_1" #(3)!
          connectTimeout: "5s" #(4)!
          readTimeout: "2m" #(5)!
          useEnvProxy: false #(6)!
          proxy:
            host: "localhost" #(7)!
            port: 8090  #(8)!
            user: "user"  #(9)!
            password: "password" #(10)!
            nonProxyHosts: [ "host1", "host2" ] #(11)!
        ```

        1. Следовать ли [HTTP-перенаправлениям](https://developer.mozilla.org/ru/docs/Web/HTTP/Redirections) (по умолчанию: `true`)
        2. Повторять ли запрос после сбоя соединения; это может влиять на максимальное время установки соединения (по умолчанию: `true`)
        3. Максимальная используемая версия протокола `HTTP`, доступные значения: `HTTP_1_1` / `HTTP_2` / `HTTP_3` (по умолчанию: `HTTP_1_1`)
        4. Максимальное время установки соединения (по умолчанию: `5s`)
        5. Максимальное время чтения ответа (по умолчанию: `2m`)
        6. Использовать ли переменные окружения `https_proxy` / `HTTPS_PROXY` / `http_proxy` / `HTTP_PROXY` и `no_proxy` / `NO_PROXY` для настройки прокси (по умолчанию: `false`)
        7. Хост прокси-сервера (обязательный, если секция `proxy` присутствует, без значения по умолчанию)
        8. Порт прокси-сервера (обязательный, если секция `proxy` присутствует, без значения по умолчанию)
        9. Пользователь прокси-сервера (опционально, без значения по умолчанию)
        10. Пароль прокси-сервера (опционально, без значения по умолчанию)
        11. Хосты, которые исключаются из проксирования (опционально, без значения по умолчанию)

Телеметрия **не** настраивается в секции транспорта: логирование, метрики и трассировка настраиваются для каждого
декларативного клиента по пути `httpClient.<clientName>.telemetry`, смотрите [Конфигурацию клиента](#client-configuration).

Метрики модуля описаны в разделе [Описание метрик](metrics.md#http-client).

#### Конфигуратор { #configurer }

Построитель транспорта настраивается компонентом `Configurer<OkHttpClient.Builder>`.
Kora применяет его последним, уже после собственной настройки:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeConfigurer implements Configurer<OkHttpClient.Builder> {

        @Override
        public OkHttpClient.Builder configure(OkHttpClient.Builder builder) {
            return builder.callTimeout(Duration.ofSeconds(30));
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeConfigurer : Configurer<OkHttpClient.Builder> {

        override fun configure(builder: OkHttpClient.Builder): OkHttpClient.Builder {
            return builder.callTimeout(Duration.ofSeconds(30))
        }
    }
    ```

`Configurer` находится в пакете `io.koraframework.common` и является общим контрактом настройки всех транспортов Kora.

## Apache HttpClient { #apache-httpclient }

Реализация `HTTP`-клиента на базе [Apache HttpClient 5](https://hc.apache.org/httpcomponents-client-5.5.x/).
Используется классический (блокирующий) API и пул соединений, что напрямую соответствует синхронному контракту клиента Kora.

### Подключение { #dependency-2 }

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "io.koraframework:http-client-apache"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends ApacheHttpClientModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("io.koraframework:http-client-apache")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : ApacheHttpClientModule
    ```

Реализацией интерфейса `HttpClient` выступает `ApacheHttpClient` из пакета `io.koraframework.http.client.apache`.

### Конфигурация { #configuration-2 }

Основные параметры конфигурации Apache HttpClient:

===! ":material-code-json: `Hocon`"

    ```javascript
    httpClient {
        connectTimeout = "5s" //(1)!
        readTimeout = "2m" //(2)!
    }
    ```

    1.  Максимальное время установки соединения (по умолчанию: `5s`)
    2.  Максимальное время чтения ответа, отображается на response timeout Apache (по умолчанию: `2m`)

=== ":simple-yaml: `YAML`"

    ```yaml
    httpClient:
      connectTimeout: "5s" #(1)!
      readTimeout: "2m" #(2)!
    ```

    1.  Максимальное время установки соединения (по умолчанию: `5s`)
    2.  Максимальное время чтения ответа, отображается на response timeout Apache (по умолчанию: `2m`)

??? note "Полная конфигурация"

    Пример полной конфигурации, описанной в классах `ApacheHttpClientConfig`
    и `HttpClientConfig` (указаны значения по умолчанию либо примерные значения):

    ===! ":material-code-json: `Hocon`"

        ```javascript
        httpClient {
            apache {
                followRedirects = true //(1)!
                maxRedirects = 3 //(2)!
                maxConnections = 1000 //(3)!
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
        }
        ```

        1. Следовать ли [HTTP-перенаправлениям](https://developer.mozilla.org/ru/docs/Web/HTTP/Redirections) (по умолчанию: `true`)
        2. Максимальное количество перенаправлений для одного запроса (по умолчанию: `3`)
        3. Максимальное количество соединений в пуле, применяется и суммарно, и на маршрут (по умолчанию: количество доступных процессоров, умноженное на `250`)
        4. Максимальное время установки соединения (по умолчанию: `5s`)
        5. Максимальное время чтения ответа (по умолчанию: `2m`)
        6. Использовать ли переменные окружения `https_proxy` / `HTTPS_PROXY` / `http_proxy` / `HTTP_PROXY` и `no_proxy` / `NO_PROXY` для настройки прокси (по умолчанию: `false`)
        7. Хост прокси-сервера (обязательный, если секция `proxy` присутствует, без значения по умолчанию)
        8. Порт прокси-сервера (обязательный, если секция `proxy` присутствует, без значения по умолчанию)
        9. Пользователь прокси-сервера (опционально, без значения по умолчанию)
        10. Пароль прокси-сервера (опционально, без значения по умолчанию)
        11. Хосты, которые исключаются из проксирования (опционально, без значения по умолчанию)

    === ":simple-yaml: `YAML`"

        ```yaml
        httpClient:
          apache:
            followRedirects: true #(1)!
            maxRedirects: 3 #(2)!
            maxConnections: 1000 #(3)!
          connectTimeout: "5s" #(4)!
          readTimeout: "2m" #(5)!
          useEnvProxy: false #(6)!
          proxy:
            host: "localhost" #(7)!
            port: 8090  #(8)!
            user: "user"  #(9)!
            password: "password" #(10)!
            nonProxyHosts: [ "host1", "host2" ] #(11)!
        ```

        1. Следовать ли [HTTP-перенаправлениям](https://developer.mozilla.org/ru/docs/Web/HTTP/Redirections) (по умолчанию: `true`)
        2. Максимальное количество перенаправлений для одного запроса (по умолчанию: `3`)
        3. Максимальное количество соединений в пуле, применяется и суммарно, и на маршрут (по умолчанию: количество доступных процессоров, умноженное на `250`)
        4. Максимальное время установки соединения (по умолчанию: `5s`)
        5. Максимальное время чтения ответа (по умолчанию: `2m`)
        6. Использовать ли переменные окружения `https_proxy` / `HTTPS_PROXY` / `http_proxy` / `HTTP_PROXY` и `no_proxy` / `NO_PROXY` для настройки прокси (по умолчанию: `false`)
        7. Хост прокси-сервера (обязательный, если секция `proxy` присутствует, без значения по умолчанию)
        8. Порт прокси-сервера (обязательный, если секция `proxy` присутствует, без значения по умолчанию)
        9. Пользователь прокси-сервера (опционально, без значения по умолчанию)
        10. Пароль прокси-сервера (опционально, без значения по умолчанию)
        11. Хосты, которые исключаются из проксирования (опционально, без значения по умолчанию)

#### Конфигуратор { #configurer-2 }

Транспорт Apache принимает два конфигуратора: `Configurer<RequestConfig.Builder>` для настроек запроса по умолчанию
и `Configurer<HttpClientBuilder>` для самого клиента. Оба опциональны:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeRequestConfigurer implements Configurer<RequestConfig.Builder> {

        @Override
        public RequestConfig.Builder configure(RequestConfig.Builder builder) {
            return builder.setConnectionRequestTimeout(1, TimeUnit.SECONDS);
        }
    }

    @Component
    public final class SomeClientConfigurer implements Configurer<HttpClientBuilder> {

        @Override
        public HttpClientBuilder configure(HttpClientBuilder builder) {
            return builder.setUserAgent("my-service");
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeRequestConfigurer : Configurer<RequestConfig.Builder> {

        override fun configure(builder: RequestConfig.Builder): RequestConfig.Builder {
            return builder.setConnectionRequestTimeout(1, TimeUnit.SECONDS)
        }
    }

    @Component
    class SomeClientConfigurer : Configurer<HttpClientBuilder> {

        override fun configure(builder: HttpClientBuilder): HttpClientBuilder {
            return builder.setUserAgent("my-service")
        }
    }
    ```

## Java клиент { #native-client }

Реализация `HTTP`-клиента на базе встроенного в [JDK](https://openjdk.org/groups/net/httpclient/intro.html) клиента.
Kora запускает его на исполнителе виртуальных потоков, поэтому у транспорта нет собственных настроек пула потоков.

### Подключение { #dependency-3 }

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "io.koraframework:http-client-jdk"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends JdkHttpClientModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("io.koraframework:http-client-jdk")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : JdkHttpClientModule
    ```

Реализацией интерфейса `HttpClient` выступает `JdkHttpClient` из пакета `io.koraframework.http.client.jdk`.

### Конфигурация { #configuration-3 }

Основные параметры конфигурации JDK HttpClient:

===! ":material-code-json: `Hocon`"

    ```javascript
    httpClient {
        connectTimeout = "5s" //(1)!
        readTimeout = "2m" //(2)!
    }
    ```

    1.  Максимальное время установки соединения (по умолчанию: `5s`)
    2.  Максимальное время чтения ответа (по умолчанию: `2m`)

=== ":simple-yaml: `YAML`"

    ```yaml
    httpClient:
      connectTimeout: "5s" #(1)!
      readTimeout: "2m" #(2)!
    ```

    1.  Максимальное время установки соединения (по умолчанию: `5s`)
    2.  Максимальное время чтения ответа (по умолчанию: `2m`)

??? note "Полная конфигурация"

    Пример полной конфигурации, описанной в классах `JdkHttpClientConfig`
    и `HttpClientConfig` (указаны значения по умолчанию либо примерные значения):

    ===! ":material-code-json: `Hocon`"

        ```javascript
        httpClient {
            jdk {
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

        1. Следовать ли [HTTP-перенаправлениям](https://developer.mozilla.org/ru/docs/Web/HTTP/Redirections) (по умолчанию: `true`)
        2. Какую версию протокола `HTTP` использовать, доступные значения: `HTTP_1_1` / `HTTP_2` (по умолчанию: `HTTP_1_1`)
        3. Максимальное время установки соединения (по умолчанию: `5s`)
        4. Максимальное время чтения ответа (по умолчанию: `2m`)
        5. Использовать ли переменные окружения `https_proxy` / `HTTPS_PROXY` / `http_proxy` / `HTTP_PROXY` и `no_proxy` / `NO_PROXY` для настройки прокси (по умолчанию: `false`)
        6. Хост прокси-сервера (обязательный, если секция `proxy` присутствует, без значения по умолчанию)
        7. Порт прокси-сервера (обязательный, если секция `proxy` присутствует, без значения по умолчанию)
        8. Пользователь прокси-сервера (опционально, без значения по умолчанию)
        9. Пароль прокси-сервера (опционально, без значения по умолчанию)
        10. Хосты, которые исключаются из проксирования (опционально, без значения по умолчанию)

    === ":simple-yaml: `YAML`"

        ```yaml
        httpClient:
          jdk:
            followRedirects: true #(1)!
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
        ```

        1. Следовать ли [HTTP-перенаправлениям](https://developer.mozilla.org/ru/docs/Web/HTTP/Redirections) (по умолчанию: `true`)
        2. Какую версию протокола `HTTP` использовать, доступные значения: `HTTP_1_1` / `HTTP_2` (по умолчанию: `HTTP_1_1`)
        3. Максимальное время установки соединения (по умолчанию: `5s`)
        4. Максимальное время чтения ответа (по умолчанию: `2m`)
        5. Использовать ли переменные окружения `https_proxy` / `HTTPS_PROXY` / `http_proxy` / `HTTP_PROXY` и `no_proxy` / `NO_PROXY` для настройки прокси (по умолчанию: `false`)
        6. Хост прокси-сервера (обязательный, если секция `proxy` присутствует, без значения по умолчанию)
        7. Порт прокси-сервера (обязательный, если секция `proxy` присутствует, без значения по умолчанию)
        8. Пользователь прокси-сервера (опционально, без значения по умолчанию)
        9. Пароль прокси-сервера (опционально, без значения по умолчанию)
        10. Хосты, которые исключаются из проксирования (опционально, без значения по умолчанию)

#### Конфигуратор { #configurer-3 }

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeConfigurer implements Configurer<java.net.http.HttpClient.Builder> {

        @Override
        public java.net.http.HttpClient.Builder configure(java.net.http.HttpClient.Builder builder) {
            return builder.sslContext(SSLContext.getDefault());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeConfigurer : Configurer<java.net.http.HttpClient.Builder> {

        override fun configure(builder: java.net.http.HttpClient.Builder): java.net.http.HttpClient.Builder {
            return builder.sslContext(SSLContext.getDefault())
        }
    }
    ```

## Декларативный клиент { #client-declarative }

Для создания декларативного клиента предлагается использовать специальные аннотации:

* `@HttpClient` - указывает, что интерфейс является декларативным HTTP-клиентом
* `@HttpRoute` - указывает [тип HTTP-запроса](https://developer.mozilla.org/ru/docs/Web/HTTP/Methods) и путь запроса

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

`HttpMethod` — это контейнер строковых констант (`GET`, `HEAD`, `POST`, `PUT`, `DELETE`, `CONNECT`, `OPTIONS`, `TRACE`, `PATCH`, `QUERY`),
поэтому запись `method = "GET"` также корректна.

Интерфейс клиента может наследовать другие интерфейсы: маршруты, объявленные в родителе, тоже будут реализованы,
а переопределенный в клиенте метод заменяет унаследованный маршрут.

### Конфигурация клиента { #client-configuration }

По умолчанию конфигурация конкретной реализации `@HttpClient` ищется по пути `httpClient.{имя класса с маленькой буквы}`.
Если путь требуется указать явно, он передается значением аннотации:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpClient("httpClient.someClient") //(1)!
    public interface SomeClient {

        @HttpRoute(method = HttpMethod.GET, path = "/hello/world")
        void hello();
    }
    ```

    1. Путь к конфигурации именно этого клиента

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpClient("httpClient.someClient") //(1)!
    interface SomeClient {

        @HttpRoute(method = HttpMethod.GET, path = "/hello/world")
        fun hello()
    }
    ```

    1. Путь к конфигурации именно этого клиента

В `@HttpClient` также можно указать теги внедряемых компонентов:

* `httpClientTag` — тег для выбора конкретного транспортного `HttpClient`, когда в графе есть несколько реализаций с разными `@Tag`
* `telemetryTag` — тег для выбора конкретной фабрики `HttpClientTelemetryFactory`

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpClient(
        value = "httpClient.someClient",
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
        value = "httpClient.someClient",
        httpClientTag = CustomTransport::class,
        telemetryTag = CustomTelemetry::class
    )
    interface SomeClient {

        @HttpRoute(method = HttpMethod.GET, path = "/hello/world")
        fun hello()
    }
    ```

Эти теги выбирают, **какой** компонент внедрить, когда в графе присутствует несколько. Вторая часть — предоставить этот компонент
под **тем же** `@Tag`. Например, чтобы дать одному клиенту выделенный транспорт (отдельный пул соединений, другие таймауты,
свой `OkHttpConfigurer` и т.д.), предоставьте `HttpClient` с тегом и сошлитесь на тот же класс-тег из `httpClientTag`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public final class CustomTransport { } //(1)!

    @Module
    public interface TransportModule {

        @Tag(CustomTransport.class) //(2)!
        default HttpClient customHttpClient(okhttp3.OkHttpClient okHttp) {
            return new OkHttpClient(okHttp); //(3)!
        }
    }
    ```

    1. Класс-маркер, используемый только как тег
    2. Предоставляется под тем же тегом, на который ссылается `httpClientTag`
    3. `ru.tinkoff.kora.http.client.ok.OkHttpClient` — транспорт Kora, оборачивающий `okhttp3.OkHttpClient`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class CustomTransport //(1)!

    @Module
    interface TransportModule {

        @Tag(CustomTransport::class) //(2)!
        fun customHttpClient(okHttp: okhttp3.OkHttpClient): HttpClient {
            return OkHttpClient(okHttp) //(3)!
        }
    }
    ```

    1. Класс-маркер, используемый только как тег
    2. Предоставляется под тем же тегом, на который ссылается `httpClientTag`
    3. `ru.tinkoff.kora.http.client.ok.OkHttpClient` — транспорт Kora, оборачивающий `okhttp3.OkHttpClient`

`telemetryTag` работает так же для `HttpClientTelemetryFactory` с тегом. Если тег не указан, используются транспорт и телеметрия по умолчанию.

Основные параметры конфигурации декларативного клиента:

===! ":material-code-json: `Hocon`"

    ```javascript
    httpClient {
        someClient {
            url = "https://localhost:8090" //(1)!
            requestTimeout = "10s" //(2)!
        }
    }
    ```

    1.  Базовый `URL` сервиса, куда будут отправляться запросы (обязательный, без значения по умолчанию)
    2.  Максимальное время запроса (опционально, без значения по умолчанию)

=== ":simple-yaml: `YAML`"

    ```yaml
    httpClient:
      someClient:
        url: "https://localhost:8090" #(1)!
        requestTimeout: "10s" #(2)!
    ```

    1.  Базовый `URL` сервиса, куда будут отправляться запросы (обязательный, без значения по умолчанию)
    2.  Максимальное время запроса (опционально, без значения по умолчанию)

??? note "Полная конфигурация"

    Пример конфигурации для пути `httpClient.someClient`, описанной в классах `DeclarativeHttpClientConfig`
    и `HttpClientTelemetryConfig`:

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
                        pathFull = false //(7)!
                        maxRequestBodyLogSize = "2MiB" //(8)!
                        maxResponseBodyLogSize = "2MiB" //(9)!
                    }
                    metrics {
                        enabled = false //(10)!
                        slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(11)!
                        tags = { // (12)!
                            "key1" = "value1"
                            "key2" = "value2"
                        }
                    }
                    tracing {
                        enabled = true //(13)!
                        pathFull = true //(14)!
                        attributes = { // (15)!
                            "key1" = "value1"
                            "key2" = "value2"
                        }
                    }
                }
            }
        }
        ```

        1. Базовый `URL` сервиса, куда будут отправляться запросы (обязательный, без значения по умолчанию)
        2. Максимальное время запроса: может включать разрешение `DNS`, установку соединения, запись тела запроса, обработку на сервере и чтение тела ответа. Если вызову требуются перенаправления или повторы, все они должны уложиться в один такой период (опционально, без значения по умолчанию)
        3. Включает логирование модуля (по умолчанию: `false`)
        4. Маска, которой скрываются указанные заголовки и параметры запроса или ответа (по умолчанию: `***`)
        5. Список параметров запроса, которые требуется скрывать (по умолчанию: `[]`)
        6. Список заголовков запроса или ответа, которые требуется скрывать (по умолчанию: `[ "authorization", "cookie", "set-cookie" ]`)
        7. Писать ли в лог полный путь запроса вместо шаблона маршрута; если значение не указано, полный путь пишется только на уровне `TRACE`, а в остальных случаях используется шаблон (опционально, без значения по умолчанию)
        8. Максимальный размер тела запроса, которое еще записывается в лог; тело большего размера пропускается с предупреждением (по умолчанию: `2MiB`)
        9. Максимальный размер тела ответа, которое еще записывается в лог; тело большего размера пропускается с предупреждением (по умолчанию: `2MiB`)
        10. Включает метрики модуля (по умолчанию: `false`)
        11. Настраивает [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) корзины в миллисекундах для метрик (по умолчанию: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
        12. Настраивает теги метрик (по умолчанию: `{}`)
        13. Включает трассировку модуля (по умолчанию: `true`)
        14. Записывать ли в span атрибут `url.full` вместо только `url.path` (по умолчанию: `true`)
        15. Настраивает атрибуты трассировки (по умолчанию: `{}`)

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
                pathFull: false #(7)!
                maxRequestBodyLogSize: "2MiB" #(8)!
                maxResponseBodyLogSize: "2MiB" #(9)!
              metrics:
                enabled: false #(10)!
                slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(11)!
                tags: #(12)!
                  key1: value1
                  key2: value2
              tracing:
                enabled: true #(13)!
                pathFull: true #(14)!
                attributes: #(15)!
                  key1: value1
                  key2: value2
        ```

        1. Базовый `URL` сервиса, куда будут отправляться запросы (обязательный, без значения по умолчанию)
        2. Максимальное время запроса: может включать разрешение `DNS`, установку соединения, запись тела запроса, обработку на сервере и чтение тела ответа. Если вызову требуются перенаправления или повторы, все они должны уложиться в один такой период (опционально, без значения по умолчанию)
        3. Включает логирование модуля (по умолчанию: `false`)
        4. Маска, которой скрываются указанные заголовки и параметры запроса или ответа (по умолчанию: `***`)
        5. Список параметров запроса, которые требуется скрывать (по умолчанию: `[]`)
        6. Список заголовков запроса или ответа, которые требуется скрывать (по умолчанию: `[ "authorization", "cookie", "set-cookie" ]`)
        7. Писать ли в лог полный путь запроса вместо шаблона маршрута; если значение не указано, полный путь пишется только на уровне `TRACE`, а в остальных случаях используется шаблон (опционально, без значения по умолчанию)
        8. Максимальный размер тела запроса, которое еще записывается в лог; тело большего размера пропускается с предупреждением (по умолчанию: `2MiB`)
        9. Максимальный размер тела ответа, которое еще записывается в лог; тело большего размера пропускается с предупреждением (по умолчанию: `2MiB`)
        10. Включает метрики модуля (по умолчанию: `false`)
        11. Настраивает [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) корзины в миллисекундах для метрик (по умолчанию: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
        12. Настраивает теги метрик (по умолчанию: `{}`)
        13. Включает трассировку модуля (по умолчанию: `true`)
        14. Записывать ли в span атрибут `url.full` вместо только `url.path` (по умолчанию: `true`)
        15. Настраивает атрибуты трассировки (по умолчанию: `{}`)

???+ warning "Метрики и логирование выключены по умолчанию"

    В Kora 2.0 `telemetry.metrics.enabled` и `telemetry.logging.enabled` по умолчанию `false`, а `telemetry.tracing.enabled` — `true`.
    При выключенных метриках ничего не падает и ничего не пишется в лог — метрика `http.client.request.duration` просто не появляется.
    Включайте их явно для каждого клиента.

### Конфигурация метода { #method-configuration }

Для конкретного метода часть параметров настраивается отдельно. Путь конфигурации метода складывается из пути клиента и имени метода:
если путь клиента `httpClient.someClient`, то итоговый путь для метода `hello` — `httpClient.someClient.hello`.

Конфигурация метода накладывается поверх конфигурации клиента: `requestTimeout` метода заменяет значение клиента,
а настройки телеметрии метода переопределяют только явно указанные поля.

Основные параметры конфигурации метода:

===! ":material-code-json: `Hocon`"

    ```javascript
    httpClient {
        someClient {
            hello {
                requestTimeout = "10s" //(1)!
            }
        }
    }
    ```

    1.  Максимальное время запроса (опционально, без значения по умолчанию)

=== ":simple-yaml: `YAML`"

    ```yaml
    httpClient:
      someClient:
        hello:
          requestTimeout: "10s" #(1)!
    ```

    1.  Максимальное время запроса (опционально, без значения по умолчанию)

??? note "Полная конфигурация"

    Пример полной конфигурации метода, описанной в классе `HttpClientOperationConfig`.
    Все поля опциональны: пропущенное поле наследует значение клиента.

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
                            pathFull = false //(6)!
                            maxRequestBodyLogSize = "2MiB" //(7)!
                            maxResponseBodyLogSize = "2MiB" //(8)!
                        }
                        metrics {
                            enabled = false //(9)!
                            slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(10)!
                            tags = { // (11)!
                                "key1" = "value1"
                                "key2" = "value2"
                            }
                        }
                        tracing {
                            enabled = true //(12)!
                            pathFull = true //(13)!
                            attributes = { // (14)!
                                "key1" = "value1"
                                "key2" = "value2"
                            }
                        }
                    }
                }
            }
        }
        ```

        1. Максимальное время запроса: может включать разрешение `DNS`, установку соединения, запись тела запроса, обработку на сервере и чтение тела ответа. Если вызову требуются перенаправления или повторы, все они должны уложиться в один такой период (опционально, наследует значение клиента)
        2. Включает логирование модуля (опционально, наследует значение клиента)
        3. Маска, которой скрываются указанные заголовки и параметры запроса или ответа (опционально, наследует значение клиента)
        4. Список параметров запроса, которые требуется скрывать (опционально, наследует значение клиента)
        5. Список заголовков запроса или ответа, которые требуется скрывать (опционально, наследует значение клиента)
        6. Писать ли в лог полный путь запроса вместо шаблона маршрута (опционально, наследует значение клиента)
        7. Максимальный размер тела запроса, которое еще записывается в лог (опционально, наследует значение клиента)
        8. Максимальный размер тела ответа, которое еще записывается в лог (опционально, наследует значение клиента)
        9. Включает метрики модуля (опционально, наследует значение клиента)
        10. Настраивает [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) корзины в миллисекундах для метрик (опционально, наследует значение клиента)
        11. Настраивает теги метрик (опционально, наследует значение клиента)
        12. Включает трассировку модуля (опционально, наследует значение клиента)
        13. Записывать ли в span атрибут `url.full` вместо только `url.path` (опционально, наследует значение клиента)
        14. Настраивает атрибуты трассировки (опционально, наследует значение клиента)

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
                  pathFull: false #(6)!
                  maxRequestBodyLogSize: "2MiB" #(7)!
                  maxResponseBodyLogSize: "2MiB" #(8)!
                metrics:
                  enabled: false #(9)!
                  slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(10)!
                  tags: #(11)!
                    key1: value1
                    key2: value2
                tracing:
                  enabled: true #(12)!
                  pathFull: true #(13)!
                  attributes: #(14)!
                    key1: value1
                    key2: value2
        ```

        1. Максимальное время запроса: может включать разрешение `DNS`, установку соединения, запись тела запроса, обработку на сервере и чтение тела ответа. Если вызову требуются перенаправления или повторы, все они должны уложиться в один такой период (опционально, наследует значение клиента)
        2. Включает логирование модуля (опционально, наследует значение клиента)
        3. Маска, которой скрываются указанные заголовки и параметры запроса или ответа (опционально, наследует значение клиента)
        4. Список параметров запроса, которые требуется скрывать (опционально, наследует значение клиента)
        5. Список заголовков запроса или ответа, которые требуется скрывать (опционально, наследует значение клиента)
        6. Писать ли в лог полный путь запроса вместо шаблона маршрута (опционально, наследует значение клиента)
        7. Максимальный размер тела запроса, которое еще записывается в лог (опционально, наследует значение клиента)
        8. Максимальный размер тела ответа, которое еще записывается в лог (опционально, наследует значение клиента)
        9. Включает метрики модуля (опционально, наследует значение клиента)
        10. Настраивает [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) корзины в миллисекундах для метрик (опционально, наследует значение клиента)
        11. Настраивает теги метрик (опционально, наследует значение клиента)
        12. Включает трассировку модуля (опционально, наследует значение клиента)
        13. Записывать ли в span атрибут `url.full` вместо только `url.path` (опционально, наследует значение клиента)
        14. Настраивает атрибуты трассировки (опционально, наследует значение клиента)

### Запрос { #request }

В этом разделе описаны преобразования `HTTP`-запроса для декларативного `HTTP`-клиента.
Параметры запроса задаются специальными аннотациями.

#### Преобразование параметров { #string-parameter-converter }

`HttpClientParameterWriter<T>` преобразует значение параметра в строку, прежде чем Kora подставит его в путь, параметр запроса,
заголовок или куки. У интерфейса один метод:

```java
public interface HttpClientParameterWriter<T> {
    String convert(T value);
}
```

`String`, `Integer`, `Long`, `Boolean` и примитивы Java записываются напрямую и вообще не требуют писателя.
Для любого другого типа Kora ищет компонент `HttpClientParameterWriter<T>` по точному типу параметра.
Если параметр имеет тип `Map<String, T>`, писатель ищется для типа значения `T`; если используется `Map<String, List<T>>`,
он применяется к каждому элементу списка; для `List<T>` / `Set<T>` / `Collection<T>` — к каждому элементу коллекции.

Встроенные писатели доступны для `Boolean`, `Short`, `Integer`, `Long`, `Double`, `Float`, `UUID`, `BigDecimal`, `BigInteger`,
`Duration`, `OffsetTime`, `OffsetDateTime`, `LocalTime`, `LocalDate`, `LocalDateTime`, `ZonedDateTime` и `Instant`.
Типы даты и времени записываются в формате `ISO`. Для собственных типов нужно предоставить компонент `HttpClientParameterWriter<T>`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public record UserId(long value) {}

    @Module
    public interface UserIdModule {

        default HttpClientParameterWriter<UserId> userIdParameterWriter() {
            return value -> Long.toString(value.value());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    data class UserId(val value: Long)

    @Module
    interface UserIdModule {

        fun userIdParameterWriter(): HttpClientParameterWriter<UserId> {
            return HttpClientParameterWriter { value -> value.value.toString() }
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

Для перечислений есть `EnumHttpClientParameterWriter` из пакета `io.koraframework.http.client.common.request.mapper`:
он строит писатель из констант перечисления и функции преобразования, и именно его использует [генератор OpenAPI](openapi-codegen.md).

??? failure "HttpClientParameterWriter&lt;T&gt; was not found"

    Сборка падает с ошибкой `No component found for dependency: HttpClientParameterWriter<T>`.
    Либо тип собственный и компонента-писателя нет, либо у писателя есть `@Tag`, которого нет у параметра.
    Объявите компонент `HttpClientParameterWriter<T>` для этого точного типа.

#### Параметр пути { #path-parameter }

`@Path` - обозначает значение части пути запроса, сам параметр указывается в `{кавычках}` в пути,
а имя параметра указывается в `value` либо по умолчанию равно имени аргумента метода.
Значения пути кодируются в URL, поэтому пробел превращается в `%20`.

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

Каждому placeholder-у `{name}` в пути должен соответствовать параметр `@Path`, иначе сборка падает с ошибкой
`Path template contains parameters that have no matching @Path method parameter`.

#### Параметр запроса { #query-parameter }

`@Query` - значение параметра запроса, имя указывается в `value` либо по умолчанию равно имени аргумента метода.
Поддерживаются одиночные значения, `List<T>`, `Set<T>`, `Collection<T>`, `Map<String, T>` и `Map<String, List<T>>`.
Для нестроковых значений используется доступный `HttpClientParameterWriter<T>`.
Пустая коллекция отправляется как параметр без значения.

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

Параметры запроса можно отправлять в формате ключ-значение через `Map`, где ключ является именем параметра и должен быть `String`.
Если значением `Map` является список, каждый его элемент отправляется как отдельное значение того же параметра.
Если элемент списка равен `null`, параметр отправляется без значения.

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

`@Header` - значение [заголовка запроса](https://developer.mozilla.org/ru/docs/Web/HTTP/Headers), имя параметра указывается в `value` либо по умолчанию равно имени аргумента метода.
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

Заголовки можно отправлять в формате ключ-значение через `HttpHeaders` или `Map`, где ключ является именем заголовка и должен быть `String`.
Для нестроковых значений используется доступный `HttpClientParameterWriter<T>`:

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

Тело запроса указывается аргументом метода без специальных аннотаций.
Из коробки поддерживаются `byte[]`, `ByteBuffer`, `String`, `HttpBodyOutput`, `FormUrlEncoded` и `FormMultipart`,
поскольку `HttpClientRequestMapperModule` предоставляет реализации `HttpClientRequestMapper` именно для этих типов.

##### Json { #json }

Чтобы указать, что тело является `JSON` и для него требуется внедрить `JsonWriter<T>`, используя тег-аннотация `@Json`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpClient
    public interface SomeClient {

        record MyBody(String name) { }

        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        void hello(@Json MyBody body); //(1)!
    }
    ```

    1. Указывает, что тело должно быть записано как Json

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpClient
    interface SomeClient {

        data class MyBody(val name: String)

        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        fun hello(@Json body: MyBody) //(1)!
    }
    ```

    1. Указывает, что тело должно быть записано как Json

Требуется модуль [Json](json.md), а также наличие `JsonWriter<MyBody>` — обычно это достигается аннотацией `@Json` на самом типе.

##### Текстовая форма { #text-form }

Используйте `FormUrlEncoded` (из `ru.tinkoff.kora.http.common.form`) как тип аргумента тела, чтобы отправить тело с
типом содержимого `application/x-www-form-urlencoded` ([форма данных](https://www.w3.org/TR/html401/interact/forms.html#h-17.13.4.1)).
Аннотации `@Json` или `@Mapping` не требуются — для этого типа в Kora есть встроенный writer.

`FormUrlEncoded` — это набор именованных частей, где каждая часть может содержать одно или несколько значений:

* `FormUrlEncoded.FormPart(String name, String value)` — часть с одним значением
* `FormUrlEncoded.FormPart(String name, List<String> values)` — часть с несколькими значениями (поле повторяется для каждого значения)
* `new FormUrlEncoded(FormPart...)` / `new FormUrlEncoded(List<FormPart>)` / `new FormUrlEncoded(Map<String, FormPart>)` — создание формы; части с одинаковым именем объединяются в одну

Объявите метод клиента с параметром `FormUrlEncoded`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpClient
    public interface SomeClient {

        @HttpRoute(method = HttpMethod.POST, path = "/form/encoded")
        HttpResponseEntity<String> formEncoded(FormUrlEncoded body);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpClient
    interface SomeClient {

        @HttpRoute(method = HttpMethod.POST, path = "/form/encoded")
        fun formEncoded(body: FormUrlEncoded): HttpResponseEntity<String>
    }
    ```

Пример вызова метода с такой формой выглядит так:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var response = someClient.formEncoded(new FormUrlEncoded(
            new FormUrlEncoded.FormPart("name", "Bob"),
            new FormUrlEncoded.FormPart("password", "12345"),
            new FormUrlEncoded.FormPart("roles", List.of("admin", "user")) //(1)!
    ));
    ```

    1. Отправляется как `roles=admin&roles=user`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val response = someClient.formEncoded(
        FormUrlEncoded(
            FormUrlEncoded.FormPart("name", "Bob"),
            FormUrlEncoded.FormPart("password", "12345"),
            FormUrlEncoded.FormPart("roles", listOf("admin", "user")) //(1)!
        )
    )
    ```

    1. Отправляется как `roles=admin&roles=user`

##### Бинарная форма { #binary-form }

Используйте `FormMultipart` (из `ru.tinkoff.kora.http.common.form`) как тип аргумента тела, чтобы отправить тело
`multipart/form-data` ([бинарная форма](https://www.w3.org/TR/html401/interact/forms.html#h-17.13.4.2)), обычно используется для загрузки файлов вместе с текстовыми полями.
Аннотации `@Json` или `@Mapping` не требуются.

`FormMultipart` — это список частей, создаваемых через статические фабричные методы:

* `FormMultipart.data(String name, String value)` — текстовое поле
* `FormMultipart.file(String name, String fileName, String contentType, byte[] content)` — файловая часть, загруженная в память (`fileName` и `contentType` могут быть `null`)
* `FormMultipart.file(String name, String fileName, String contentType, Flow.Publisher<ByteBuffer> content)` — потоковая файловая часть для больших данных, которые не следует полностью буферизовать в памяти
* `new FormMultipart(List<? extends FormPart>)` — создание формы из частей

Объявите метод клиента с параметром `FormMultipart`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpClient
    public interface SomeClient {

        @HttpRoute(method = HttpMethod.POST, path = "/form/multipart")
        HttpResponseEntity<String> formMultipart(FormMultipart body);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpClient
    interface SomeClient {

        @HttpRoute(method = HttpMethod.POST, path = "/form/multipart")
        fun formMultipart(body: FormMultipart): HttpResponseEntity<String>
    }
    ```

Пример вызова метода с такой формой выглядит так:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var response = someClient.formMultipart(new FormMultipart(List.of(
            FormMultipart.data("field1", "some data content"), //(1)!
            FormMultipart.file("field2", "example1.txt", "text/plain",
                    "some file content".getBytes(StandardCharsets.UTF_8)) //(2)!
    )));
    ```

    1. Текстовое поле
    2. Файловая часть с именем файла и типом содержимого

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val response = someClient.formMultipart(
        FormMultipart(
            listOf(
                FormMultipart.data("field1", "some data content"), //(1)!
                FormMultipart.file(
                    "field2",
                    "example1.txt",
                    "text/plain",
                    "some file content".toByteArray(StandardCharsets.UTF_8)
                ) //(2)!
            )
        )
    )
    ```

    1. Текстовое поле
    2. Файловая часть с именем файла и типом содержимого

Метод `FormMultipart.file(String name, String fileName, HttpBodyOutput content)` отправляет часть формы потоком, а не массивом байт.

##### Свое тело { #custom-body }

Если тело требуется записать способом, отличным от стандартных механизмов,
можно использовать специальный интерфейс `HttpClientRequestMapper` для реализации собственной логики:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpClient
    public interface SomeClient {

        record UserBody(String id) {}

        final class UserRequestMapper implements HttpClientRequestMapper<UserBody> {

            @Override
            public HttpBodyOutput apply(UserBody value) {
                return HttpBody.plaintext(value.id());
            }
        }

        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        HttpResponseEntity<String> hello(@Mapping(UserRequestMapper.class) UserBody body);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpClient
    interface SomeClient {

        data class UserBody(val id: String)

        class UserRequestMapper : HttpClientRequestMapper<UserBody> {

            override fun apply(value: UserBody): HttpBodyOutput {
                return HttpBody.plaintext(value.id)
            }
        }

        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        fun hello(@Mapping(UserRequestMapper::class) body: UserBody): HttpResponseEntity<String>
    }
    ```

**Пример: сериализация Protobuf**

Обратите внимание, что `HttpBody.of` принимает сначала тип содержимого, а затем полезную нагрузку:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpClient
    public interface ProtobufClient {

        final class ProtobufRequestMapper implements HttpClientRequestMapper<MyMessage> {

            @Override
            public HttpBodyOutput apply(MyMessage value) {
                byte[] protobufBytes = value.toByteArray();
                return HttpBody.of("application/x-protobuf", protobufBytes);
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

            override fun apply(value: MyMessage): HttpBodyOutput {
                val protobufBytes = value.toByteArray()
                return HttpBody.of("application/x-protobuf", protobufBytes)
            }
        }

        @HttpRoute(method = HttpMethod.POST, path = "/message")
        fun sendMessage(@Mapping(ProtobufRequestMapper::class) message: MyMessage)
    }
    ```

???+ note "Когда мапперу нужен `@Component`"

    Маппер, указанный в `@Mapping`, который является `final` (Java) либо не `open` (Kotlin) **и** имеет единственный публичный
    конструктор без аргументов, создается самим сгенерированным клиентом — компонентом графа он быть не должен.
    Любой другой маппер — с зависимостями в конструкторе, например `JsonReader<T>`, открытый класс или класс с несколькими
    конструкторами — берется из контейнера зависимостей и потому должен быть объявлен как `@Component`.
    Ориентироваться нужно на конструктор, а не на аннотацию над методом.

#### Куки { #cookie }

`@Cookie` - значение [Cookie](https://developer.mozilla.org/ru/docs/Glossary/Cookie), имя параметра указывается в `value` либо по умолчанию равно имени аргумента метода.
Поддерживаются одиночные значения, `List<T>`, `Set<T>`, `Collection<T>`, `Map<String, T>` и готовый объект `Cookie`.
Каждая кука записывается отдельным значением заголовка `Cookie` в формате `name=value`.

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

    По умолчанию все аргументы, объявленные в методе, считаются **обязательными** (*NotNull*).

=== ":simple-kotlin: `Kotlin`"

    По умолчанию все аргументы метода, которые не используют синтаксис [Kotlin Nullability](https://kotlinlang.org/docs/null-safety.html), считаются **обязательными** (*NotNull*).

#### Необязательные параметры { #optional-parameters }

===! ":fontawesome-brands-java: `Java`"

    Если аргумент метода необязательный, то есть его может не быть,
    можно использовать аннотацию `@Nullable`:

    ```java
    @HttpClient
    public interface SomeClient {

        @HttpRoute(method = HttpMethod.GET, path = "/hello/world")
        void hello(@Nullable @Query("queryValue") String queryValue); //(1)!
    }
    ```

    1.  Kora построена на [JSpecify](https://jspecify.dev/), поэтому рекомендуется `org.jspecify.annotations.Nullable`; принимается любая аннотация с простым именем `Nullable`.

=== ":simple-kotlin: `Kotlin`"

    Предполагается использование синтаксиса [Kotlin Nullability](https://kotlinlang.org/docs/null-safety.html) и пометка такого параметра как Nullable:

    ```kotlin
    @HttpClient
    interface SomeClient {

        @HttpRoute(method = HttpMethod.GET, path = "/hello/world")
        fun hello(@Query("queryValue") queryValue: String?)
    }
    ```

Параметр запроса, заголовок или кука со значением `null` просто не попадают в запрос.

### Ответ { #response }

В разделе описано преобразование HTTP-ответа для декларативного HTTP-клиента.

#### Тело ответа { #response-body }

Kora поставляет реализации `HttpClientResponseMapper` для ограниченного набора типов, все они объявлены в `HttpClientResponseMapperModule`:

| Тип возврата | Требует |
|---|---|
| `void` | ничего, тело не читается |
| `String` | ничего |
| `byte[]` | ничего |
| `ByteBuffer` | ничего |
| `HttpBodyInput` | ничего, тело остается потоком |
| `T` с `@Json` | `JsonReader<T>` |
| `HttpResponseEntity<T>` | `HttpClientResponseMapper<T>` для полезной нагрузки |
| `Either<T, E>` | по одному `HttpClientResponseMapper` для `T` и для `E` |

Для любого другого типа требуется собственный маппер, смотрите [Свой ответ](#custom-response).

##### Json { #json-2 }

Если тело требуется читать как Json, над методом нужно использовать аннотацию `@Json`.

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

    1. Указывает, что ответ должен быть прочитан как Json

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpClient
    interface SomeClient {

        data class MyResponse(val name: String)

        @Json //(1)!
        @HttpRoute(method = HttpMethod.GET, path = "/hello/world")
        fun hello(): MyResponse
    }
    ```

    1. Указывает, что ответ должен быть прочитан как Json

Требуется модуль [Json](json.md).

##### Ответ с метаданными { #response-entity }

Если нужно прочитать тело и вдобавок получить заголовки и код статуса ответа,
предназначен `HttpResponseEntity` — обертка над телом ответа, которая предоставляет `code()`, `headers()` и `body()`.

Ниже пример, аналогичный примеру с Json, но с оберткой `HttpResponseEntity`:

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

        data class MyResponse(val name: String)

        @Json
        @HttpRoute(method = HttpMethod.GET, path = "/hello/world")
        fun hello(): HttpResponseEntity<MyResponse>
    }
    ```

Обертку Kora строит сама из маппера полезной нагрузки, поэтому для `HttpResponseEntity<Void>` — обычного приема, когда от ответа
нужен только код статуса, — в графе должен быть `HttpClientResponseMapper<Void>`. Встроенного нет, поэтому его объявляют компонентом
и **не** указывают через `@Mapping`: с `@Mapping` маппер обязан произвести весь тип `HttpResponseEntity<Void>`,
тогда как шаблонная фабрика фреймворка ждет маппер полезной нагрузки и оборачивает его в entity сама.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpClient("httpClient.userApi")
    public interface UserApiClient {

        @Component
        final class VoidResponseMapper implements HttpClientResponseMapper<Void> {

            @Override
            public Void apply(HttpClientResponse response) throws IOException {
                try (var body = response.body()) {
                    body.asInputStream().readAllBytes();
                }
                return null;
            }
        }

        @HttpRoute(method = HttpMethod.DELETE, path = "/users/{userId}")
        HttpResponseEntity<Void> deleteUser(@Path String userId);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpClient("httpClient.userApi")
    interface UserApiClient {

        @Component
        class VoidResponseMapper : HttpClientResponseMapper<Void> {

            override fun apply(response: HttpClientResponse): Void? {
                response.body().use { body ->
                    body.asInputStream().readAllBytes()
                }
                return null
            }
        }

        @HttpRoute(method = HttpMethod.DELETE, path = "/users/{userId}")
        fun deleteUser(@Path userId: String): HttpResponseEntity<Void>
    }
    ```

Без этого компонента сборка падает с ошибкой `No component found for dependency: HttpClientResponseMapper<java.lang.Void>`.

##### Either { #either }

`Either<T, E>` описывает вызов, для которого неуспешный код статуса является нормальным исходом, а не исключением.
Ответ `2xx` Kora преобразует маппером типа `T` в `Either.Left`, любой другой код статуса — маппером типа `E` в `Either.Right`,
и `HttpClientResponseException` для такого метода никогда не бросается.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpClient
    public interface SomeClient {

        record Success(String id) {}

        record Error(String message) {}

        @HttpRoute(method = HttpMethod.GET, path = "/users/{id}")
        Either<@Json Success, @Json Error> get(@Path String id); //(1)!
    }
    ```

    1. `@Json` здесь используется как аннотация над типом, поэтому успешную и ошибочную полезные нагрузки можно помечать независимо

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpClient
    interface SomeClient {

        data class Success(val id: String)

        data class Error(val message: String)

        @HttpRoute(method = HttpMethod.GET, path = "/users/{id}")
        fun get(@Path id: String): Either<@Json Success, @Json Error> //(1)!
    }
    ```

    1. `@Json` здесь используется как аннотация над типом, поэтому успешную и ошибочную полезные нагрузки можно помечать независимо

`Either` предоставляет `isLeft()` / `isRight()` и nullable-аксессоры `left()` / `right()`.
Также поддерживается `HttpResponseEntity<Either<T, E>>`, когда дополнительно нужны код статуса и заголовки.

#### Свой ответ { #custom-response }

Если ответ нужно прочитать иначе, можно использовать специальный интерфейс `HttpClientResponseMapper`:

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

???+ warning "Маппер из `@Mapping` обрабатывает любой код статуса"

    Если у метода объявлен `@Mapping`, Kora перестает проверять успешность кода статуса и передает мапперу **любой** ответ,
    включая `4xx` и `5xx`. Если неуспешный код должен оставаться ошибкой, бросайте исключение из маппера сами.
    Аннотация `@Tag` над методом лишь выбирает, какой компонент `HttpClientResponseMapper` будет внедрен: проверка на `2xx`
    при этом сохраняется, и неуспешный код по-прежнему приводит к `HttpClientResponseException`.

**Пример: обработка ошибок в маппере**

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpClient
    public interface ApiClient {

        record ApiResponse(String status, String data) {}

        @Component
        final class SafeResponseMapper implements HttpClientResponseMapper<ApiResponse> {

            private final JsonReader<ApiResponse> jsonReader;

            public SafeResponseMapper(JsonReader<ApiResponse> jsonReader) {
                this.jsonReader = jsonReader;
            }

            @Override
            public ApiResponse apply(HttpClientResponse response) throws IOException {
                int code = response.code();
                final byte[] body;
                try (var is = response.body().asInputStream()) {
                    body = is.readAllBytes();
                }

                if (code >= 400) {
                    // Обработка ошибки: логирование или выброс исключения
                    throw new HttpClientResponseException(code, response.headers(), body);
                }

                if (body.length == 0) {
                    return null;
                }
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

        data class ApiResponse(val status: String, val data: String)

        @Component
        class SafeResponseMapper(
            private val jsonReader: JsonReader<ApiResponse>
        ) : HttpClientResponseMapper<ApiResponse> {

            override fun apply(response: HttpClientResponse): ApiResponse {
                val code = response.code()
                val body = response.body().asInputStream().use { it.readAllBytes() }

                if (code >= 400) {
                    // Обработка ошибки: логирование или выброс исключения
                    throw HttpClientResponseException(code, response.headers(), body)
                }

                if (body.isEmpty()) {
                    return null
                }
            }
        }

        @HttpRoute(method = HttpMethod.GET, path = "/api/data")
        @Mapping(SafeResponseMapper::class)
        fun getData(): ApiResponse
    }
    ```

Этот маппер принимает `JsonReader` в конструкторе, поэтому он является компонентом графа и помечен `@Component`.

#### Ошибка ответа { #response-error }

По умолчанию, когда не указаны ни маппер в `@Mapping`, ни `@ResponseCodeMapper`,
преобразование применяется только для кодов ответа `2xx`.
Для всех остальных кодов бросается `HttpClientResponseException`. Он содержит [код ответа HTTP](https://developer.mozilla.org/ru/docs/Web/HTTP/Status), тело ответа и заголовки ответа.

Исключение из этого правила — `Either<T, E>` и `HttpResponseEntity<Either<T, E>>`: они преобразуют любой код статуса и никогда не бросают исключение.

#### Исключения клиента { #client-exceptions }

Все стандартные исключения `HTTP`-клиента наследуются от `HttpClientException`, который является `RuntimeException`.
Это позволяет ловить как конкретный тип ошибки, так и все ошибки клиента одним общим типом:

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
* `HttpClientConnectionException` — ошибка при установке или поддержании соединения с удаленным хостом.
* `HttpClientEncoderException` — ошибка при преобразовании пользовательского значения в тело запроса.
* `HttpClientDecoderException` — ошибка при преобразовании тела ответа в пользовательский тип.
* `HttpClientUnknownException` — прочая ошибка транспортного клиента, не попавшая в более конкретную категорию.

`HttpClientResponseException` создается методом `HttpClientResponseException.fromResponse(response)` после чтения тела ответа.
Если тело уже полностью буферизовано, оно сохраняется целиком; иначе в `getBytes()` попадают только первые `4096` байт,
чтобы неуспешный вызов не буферизовал произвольно большую страницу ошибки.

#### Преобразование по коду { #conversion-by-code }

Если требуются разные преобразования в зависимости от [кода статуса HTTP](https://developer.mozilla.org/ru/docs/Web/HTTP/Status) ответа,
можно использовать аннотацию `@ResponseCodeMapper`, чтобы задать соответствие между кодом статуса HTTP и обработчиком `HttpClientResponseMapper`.

Также можно использовать `ResponseCodeMapper.DEFAULT`, чтобы задать поведение по умолчанию для всех неперечисленных кодов HTTP.
Если для кода указан `mapper`, используется именно этот `HttpClientResponseMapper`.
Если указан `type`, Kora подбирает маппер ответа для этого типа, а затем приводит результат к типу возврата метода.
Это удобно для закрытых иерархий ответов, где разным статусам HTTP соответствуют разные подтипы результата.
Если не указано ни то, ни другое, Kora запрашивает у графа `HttpClientResponseMapper` для типа возврата метода
(`HttpClientResponseMapper<Void>` для метода с `void`).
Код статуса, который не перечислен и для которого нет записи `DEFAULT`, по-прежнему приводит к `HttpClientResponseException`.

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

        data class UserResponse(val payload: Payload?, val error: Error?) {

            data class Error(val code: Int, val message: String)

            data class Payload(val message: String)
        }

        @ResponseCodeMapper(code = ResponseCodeMapper.DEFAULT, mapper = ResponseErrorMapper::class)
        @ResponseCodeMapper(code = 200, mapper = ResponseSuccessMapper::class)
        @HttpRoute(method = HttpMethod.GET, path = "/hello/world")
        fun hello(): UserResponse
    }
    ```

В примере выше для кода статуса `200` будет использован `ResponseSuccessMapper`,
а для всех остальных кодов статуса — `ResponseErrorMapper`.

Пример с параметром `type`:

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

Если указанный `type` нельзя присвоить типу возврата метода, Kora трактует результат маппера как исключение и бросает его
вместо возврата — так ветку ошибки можно смоделировать как выбрасываемое исключение для конкретного кода статуса.

### Сигнатуры { #signatures }

Методы декларативного `HTTP`-клиента **блокирующие**:

===! ":fontawesome-brands-java: `Java`"

    Под `T` подразумевается тип возвращаемого значения. Это может быть тип тела (`void`, `String`, `byte[]`, тип с `@Json` и т.д.) либо
    [`HttpResponseEntity<T>`](#response-entity) для чтения также статуса и заголовков. Возврат `@Nullable T` допускает пустое успешное тело.

    - `T myMethod()`
    - `void myMethod()`

=== ":simple-kotlin: `Kotlin`"

    Под `T` подразумевается тип возвращаемого значения — `T`, `T?` (nullable для пустого успешного тела) или `T?`, либо `Unit`.
    `T` может быть типом тела либо [`HttpResponseEntity<T>`](#response-entity) для чтения также статуса и заголовков.

    - `myMethod(): T`

По умолчанию ответ со статусом не `2xx` бросает [`HttpClientResponseException`](#response-error) независимо от сигнатуры; используйте [`@ResponseCodeMapper`](#conversion-by-code) или [`HttpResponseEntity`](#response-entity), чтобы обрабатывать другие статусы без исключения.

???+ warning "Асинхронные сигнатуры не поддерживаются"

    В Kotlin метод клиента с `suspend` приводит к ошибке компиляции: *Suspend methods are not supported by the HTTP client generator*.
    В Java тип возврата `CompletionStage<T>` или `Mono<T>` дает только предупреждение *Method has async signature, this might not work correctly* —
    сгенерированный код все равно выполняет блокирующий вызов, и такой тип не будет удовлетворен.

    Независимые вызовы выполняйте параллельно на виртуальных потоках, например через `StructuredTaskScope`:

    ```java
    try (var scope = StructuredTaskScope.open(StructuredTaskScope.Joiner.<Object>awaitAllSuccessfulOrThrow())) {
        var profile = scope.fork(() -> profileHttpClient.getProfile(userId));
        var recommendations = scope.fork(() -> recommendationsHttpClient.getForUser(userId));
        scope.join();
        return new Dashboard(profile.get(), recommendations.get());
    }
    ```

## Перехватчики { #interceptors }

Для изменения или расширения поведения можно создавать перехватчики через интерфейс `HttpClientInterceptor`.
Перехватчики подключаются аннотацией `@InterceptWith` — либо к конкретному методу, либо ко всему интерфейсу `@HttpClient`.

```java
public interface HttpClientInterceptor {

    HttpClientResponse processRequest(InterceptChain chain, HttpClientRequest request) throws Exception; //(1)!

    interface InterceptChain {
        HttpClientResponse process(HttpClientRequest request) throws Exception; //(2)!
    }
}
```

1. Вызывается для каждого запроса перехватываемого метода
2. Передает запрос дальше по цепочке и возвращает ответ

Запрос неизменяемый, поэтому измененный запрос создается через `request.toBuilder()`.

Интерфейс получает текущий `Context`, исходящий `HttpClientRequest` и `InterceptChain`, продолжающий обработку:

```java
public interface HttpClientInterceptor {

    CompletionStage<HttpClientResponse> processRequest(Context ctx, InterceptChain chain, HttpClientRequest request) throws Exception; //(1)!

    interface InterceptChain {
        CompletionStage<HttpClientResponse> process(Context ctx, HttpClientRequest request) throws Exception; //(2)!
    }
}
```

1. Вызывается для каждого запроса, к которому подключён перехватчик
2. Продолжает цепочку (следующий перехватчик или фактический вызов транспорта)

Перехватчик может:

* **Изменить запрос перед отправкой** — пересоберите его через `request.toBuilder()` (добавить заголовок, изменить URI, заменить тело), затем передайте новый запрос в `chain.process(ctx, newRequest)`
* **Продолжить цепочку** — вернуть `chain.process(ctx, request)` без изменений
* **Замкнуть накоротко** — вернуть ответ, не вызывая `chain.process(...)` (например, кэшированный ответ)
* **Просмотреть или преобразовать ответ** — вызвать `chain.process(...)` и добавить `thenApply` / `thenCompose` / `exceptionally` к возвращённому `CompletionStage`
* **Завершить вызов ошибкой** — бросить исключение или вернуть неуспешный `CompletionStage`, прервав цепочку

Пример, добавляющий заголовок к каждому запросу и проверяющий статус ответа:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class TracingInterceptor implements HttpClientInterceptor {

        @Override
        public CompletionStage<HttpClientResponse> processRequest(Context ctx, InterceptChain chain, HttpClientRequest request) throws Exception {
            HttpClientRequest modified = request.toBuilder()
                .header("x-request-id", UUID.randomUUID().toString()) //(1)!
                .build();

            return chain.process(ctx, modified).thenApply(response -> {
                if (response.code() >= 500) {
                    // наблюдаем серверные ошибки
                }
                return response;
            });
        }
    }
    ```

    1. `request.toBuilder()` возвращает `HttpClientRequestBuilder`, инициализированный текущим запросом

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class TracingInterceptor : HttpClientInterceptor {

        override fun processRequest(
            ctx: Context,
            chain: HttpClientInterceptor.InterceptChain,
            request: HttpClientRequest
        ): CompletionStage<HttpClientResponse> {
            val modified = request.toBuilder()
                .header("x-request-id", UUID.randomUUID().toString()) //(1)!
                .build()

            return chain.process(ctx, modified).thenApply { response ->
                if (response.code() >= 500) {
                    // наблюдаем серверные ошибки
                }
                response
            }
        }
    }
    ```

    1. `request.toBuilder()` возвращает `HttpClientRequestBuilder`, инициализированный текущим запросом

Для императивного `HttpClient` перехватчик подключается через `httpClient.with(interceptor)` вместо `@InterceptWith`.

**Перехватчик на метод:**

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpClient
    public interface SomeClient {

        @Component
        final class MethodInterceptor implements HttpClientInterceptor {

            private final Component1 component1;

            public MethodInterceptor(Component1 component1) {
                this.component1 = component1;
            }

            @Override
            public HttpClientResponse processRequest(InterceptChain chain, HttpClientRequest request) throws Exception {
                component1.doSomething();
                return chain.process(request);
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

        @Component
        class MethodInterceptor(val component1: Component1) : HttpClientInterceptor {

            override fun processRequest(
                chain: HttpClientInterceptor.InterceptChain,
                request: HttpClientRequest
            ): HttpClientResponse {
                component1.doSomething()
                return chain.process(request)
            }
        }

        @InterceptWith(MethodInterceptor::class)
        @HttpRoute(method = HttpMethod.GET, path = "/hello/world")
        fun hello()
    }
    ```

Перехватчик берется из контейнера зависимостей, поэтому для него действует то же правило, что и для маппера:
`@Component` нужен тогда, когда у него есть зависимости в конструкторе.
У `@InterceptWith` также есть атрибут `tag` для выбора реализации перехватчика по тегу.

**Пример: добавление заголовка**

===! ":fontawesome-brands-java: `Java`"

    ```java
    public final class RequestIdInterceptor implements HttpClientInterceptor {

        @Override
        public HttpClientResponse processRequest(InterceptChain chain, HttpClientRequest request) throws Exception {
            var modified = request.toBuilder()
                    .header("x-request-id", UUID.randomUUID().toString())
                    .build();
            return chain.process(modified);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class RequestIdInterceptor : HttpClientInterceptor {

        override fun processRequest(
            chain: HttpClientInterceptor.InterceptChain,
            request: HttpClientRequest
        ): HttpClientResponse {
            val modified = request.toBuilder()
                .header("x-request-id", UUID.randomUUID().toString())
                .build()
            return chain.process(modified)
        }
    }
    ```

**Порядок выполнения перехватчиков:**

Перехватчики, объявленные на клиенте, выполняются раньше перехватчиков, объявленных на методе,
а в пределах одного элемента — в порядке объявления. Каждый перехватчик может:

- Изменить запрос перед отправкой
- Вызвать следующий перехватчик в цепочке (`chain.process(request)`)
- Изменить или проанализировать полученный ответ
- Бросить исключение и прервать цепочку

```
Request  → Client interceptors → Method interceptors → Telemetry → HTTP Server
Response ← Client interceptors ← Method interceptors ← Telemetry ← HTTP Server
```

### Перехватчик на клиент { #interceptor-global }

Если перехватчик должен применяться ко всем методам клиента, `@InterceptWith` указывается на интерфейсе:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpClient
    @InterceptWith(ClientInterceptor.class) //(1)!
    public interface SomeClient {

        @HttpRoute(method = HttpMethod.GET, path = "/hello")
        void hello();

        @HttpRoute(method = HttpMethod.POST, path = "/world")
        void world();
    }
    ```

    1. Применяется к каждому методу этого клиента

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpClient
    @InterceptWith(ClientInterceptor::class) //(1)!
    interface SomeClient {

        @HttpRoute(method = HttpMethod.GET, path = "/hello")
        fun hello()

        @HttpRoute(method = HttpMethod.POST, path = "/world")
        fun world()
    }
    ```

    1. Применяется к каждому методу этого клиента

Если перехватчики указаны и на клиенте, и на методе, для такого вызова применяются оба набора.
Реестра перехватчиков HTTP-клиента на все приложение не существует: перехватчик действует только там, где он назван в `@InterceptWith`.

### Авторизация { #authorization }

Kora предоставляет из коробки перехватчики для авторизации [Basic/ApiKey/Bearer/OAuth](https://swagger.io/docs/specification/authentication/).

#### Basic { #basic }

Требуется настроить перехватчик и конфигурацию для авторизации [Basic](https://swagger.io/docs/specification/authentication/basic-authentication/):

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface BasicAuthModule {

        @ConfigSource("openapiAuth.basicAuth")
        interface BasicAuthConfig {

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

Конструктор с двумя аргументами оборачивает учетные данные в `BasicAuthHttpClientTokenProvider`.
Если правила получения секретов отличаются, в конструктор можно передать собственную реализацию `HttpClientTokenProvider`.

Затем перехватчик добавляется на весь HTTP-клиент либо на конкретные методы.

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

Требуется настроить перехватчик и конфигурацию для авторизации [ApiKey](https://swagger.io/docs/specification/authentication/api-keys/).
`ApiKeyLocation` поддерживает значения `HEADER`, `QUERY` и `COOKIE`:

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

Затем перехватчик добавляется на весь HTTP-клиент либо на конкретные методы.

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

Требуется настроить перехватчик для авторизации [Bearer](https://swagger.io/docs/specification/authentication/bearer-authentication/):

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
    interface BearerAuthModule {

        fun bearerAuther(tokenProvider: HttpClientTokenProvider): BearerAuthHttpClientInterceptor {
            return BearerAuthHttpClientInterceptor(tokenProvider)
        }
    }
    ```

Предоставление токена `Bearer` реализуется самостоятельно через собственную реализацию `HttpClientTokenProvider`
либо используется конструктор, принимающий статический `Bearer Token`.

```java
public interface HttpClientTokenProvider {

    @Nullable
    String getToken(HttpClientRequest request); //(1)!
}
```

1. Если вернуть `null`, запрос остается без изменений и заголовок `Authorization` не добавляется

Затем перехватчик добавляется на весь HTTP-клиент либо на конкретные методы.

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

Авторизация через [OAuth](https://swagger.io/docs/specification/authentication/oauth2/) аналогична [Bearer](#bearer):
нужно самостоятельно реализовать `HttpClientTokenProvider` и поместить его в контейнер зависимостей.

#### Предоставление токена { #token-provider }

`HttpClientTokenProvider` — интерфейс для динамического получения токенов авторизации.
Используется, когда токен требуется обновлять либо получать из внешнего источника (например, из token endpoint OAuth2).
Метод блокирующий, поэтому токен можно получать прямо в нем.

**Пример реализации:**

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class MyTokenProvider implements HttpClientTokenProvider {

        private final OAuthClient oauthClient;
        private volatile String cachedToken;
        private volatile long tokenExpiry;

        public MyTokenProvider(OAuthClient oauthClient) {
            this.oauthClient = oauthClient;
        }

        @Override
        public String getToken(HttpClientRequest request) {
            if (cachedToken != null && System.currentTimeMillis() < tokenExpiry) {
                return cachedToken;
            }

            var response = oauthClient.refreshToken();
            this.cachedToken = response.accessToken();
            this.tokenExpiry = System.currentTimeMillis() + response.expiresIn() * 1000;
            return this.cachedToken;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class MyTokenProvider(
        private val oauthClient: OAuthClient
    ) : HttpClientTokenProvider {

        @Volatile
        private var cachedToken: String? = null

        @Volatile
        private var tokenExpiry: Long = 0

        override fun getToken(request: HttpClientRequest): String? {
            val token = cachedToken
            if (token != null && System.currentTimeMillis() < tokenExpiry) {
                return token
            }

            val response = oauthClient.refreshToken()
            cachedToken = response.accessToken()
            tokenExpiry = System.currentTimeMillis() + response.expiresIn() * 1000
            return cachedToken
        }
    }
    ```

**Использование с BearerAuthHttpClientInterceptor:**

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

[Генератор OpenAPI](openapi-codegen.md) ожидает тот же интерфейс, помеченный сгенерированным классом-маркером `ApiSecurity`.

## Обработка исключений { #exception-handling }

Во время HTTP-запросов могут возникать разные исключения. Все они наследуются от базового `HttpClientException`,
который является непроверяемым `RuntimeException` из пакета `io.koraframework.http.client.common.exception`.

**Иерархия исключений:**

```
HttpClientException
├── HttpClientTimeoutException
├── HttpClientConnectionException
├── HttpClientResponseException
├── HttpClientEncoderException
├── HttpClientDecoderException
└── HttpClientUnknownException
```

**Пример обработки:**

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeService {

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
                // Ошибка ответа: code, body, headers
                int code = e.getCode();
                byte[] body = e.getBytes();
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
                // Ошибка ответа: code, body, headers
                val code = e.code
                val body = e.bytes
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

#### Время ожидания { #timeout-exception }

Бросается, когда запрос превысил настроенное время ожидания (`requestTimeout`, `connectTimeout` или `readTimeout`).

**Причины:**

- Сервер не ответил за `requestTimeout`
- Превышено время установки соединения (`connectTimeout`)
- Превышено время чтения ответа (`readTimeout`)
- Сетевые задержки

**Рекомендации:**

- Настраивайте адекватные таймауты в конфигурации, на клиент и на метод
- Применяйте [повторы](resilient.md) для временных сбоев
- Используйте [circuit breaker](resilient.md) для защиты от каскадных отказов

#### Ошибка соединения { #connection-exception }

Бросается, когда не удается установить соединение с сервером.

**Причины:**

- Ошибка разрешения DNS
- Сервер недоступен (порт закрыт, firewall)
- Соединение отклонено
- Ошибка SSL/TLS handshake

**Рекомендации:**

- Проверяйте доступность сервиса (health check)
- Используйте переключение на резервный сервис
- Настраивайте повторы с экспоненциальной задержкой

#### Ошибка клиента и сервера { #response-exception }

Бросается, когда сервер вернул код статуса HTTP вне диапазона `2xx`, а метод не объявляет собственный маппер
через `@Mapping` или `@ResponseCodeMapper` и не возвращает `Either`.

**Доступные данные:**

- `getCode()` — код статуса HTTP (400, 404, 500 и т.д.)
- `getBytes()` — тело ответа, обрезанное до `4096` байт, если тело не было полностью буферизовано
- `getHeaders()` — заголовки ответа

**Рекомендации:**

- Используйте `@ResponseCodeMapper` для собственной обработки статусов
- Используйте `Either<T, E>`, когда неуспешный код является нормальным исходом
- Логируйте код и тело для отладки
- Разделяйте клиентские (4xx) и серверные (5xx) ошибки

#### Ошибка запроса { #encoder-exception }

Бросается при ошибке сериализации тела запроса: `HttpClientRequestMapper` тела бросил исключение.

**Причины:**

- Ошибка сериализации JSON или бинарного формата
- Некорректные данные в объекте запроса
- Сам маппер не справился со значением

**Рекомендации:**

- Проверяйте данные перед отправкой
- Убедитесь, что тип тела помечен `@Json` и для него есть `JsonWriter`
- Логируйте исходное исключение в `cause`

#### Ошибка ответа { #decoder-exception }

Бросается при ошибке десериализации тела ответа: `HttpClientResponseMapper` метода бросил исключение.

**Причины:**

- Некорректный JSON в ответе сервера
- Несовпадение схемы (сервер вернул неожиданные поля)
- Поток был закрыт или оборван

**Рекомендации:**

- Проверяйте совместимость версий API
- Логируйте тело ответа для отладки
- Используйте `@ResponseCodeMapper` для обработки иначе устроенных тел ошибок

#### Ошибка неизвестная { #unknown-exception }

Бросается при ошибке, не попадающей в остальные категории, включая любое проверяемое исключение, вышедшее из транспорта.

**Доступные данные:**

- `getCause()` — исходное исключение

**Рекомендации:**

- Всегда логируйте `cause` для диагностики
- Смотрите логи HTTP-клиента на уровне DEBUG/TRACE
- Заводите баг, если исключение воспроизводится

### Устойчивость { #resilience }

Приведённые выше рекомендации (повтор, circuit breaker, таймаут, fallback) предоставляются модулем [Resilient](resilient.md), а не самим HTTP-клиентом.
Его аннотации применяются напрямую к методам декларативного `@HttpClient`, поэтому отказоустойчивость можно добавить, не меняя места вызова:

* `@Retry` — повторить вызов при ошибке
* `@CircuitBreaker` — перестать вызывать сбоящую зависимость и быстро завершать вызовы ошибкой до её восстановления
* `@Timeout` — ограничить общее время вызова
* `@Fallback` — вернуть запасной результат при ошибке вызова

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpClient
    public interface SomeClient {

        @Retry("someClient.hello") //(1)!
        @CircuitBreaker("someClient.hello") //(2)!
        @HttpRoute(method = HttpMethod.GET, path = "/hello/world")
        HttpResponseEntity<String> hello();
    }
    ```

    1. Путь конфигурации повтора
    2. Путь конфигурации circuit breaker

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpClient
    interface SomeClient {

        @Retry("someClient.hello") //(1)!
        @CircuitBreaker("someClient.hello") //(2)!
        @HttpRoute(method = HttpMethod.GET, path = "/hello/world")
        fun hello(): HttpResponseEntity<String>
    }
    ```

    1. Путь конфигурации повтора
    2. Путь конфигурации circuit breaker

Обратите внимание на отличие от транспортного `requestTimeout` ([Конфигурация клиента](#client-configuration)): `requestTimeout` ограничивает одну HTTP-попытку,
тогда как `@Timeout` ограничивает весь вызов метода, включая повторы. Конфигурацию и семантику каждой аннотации см. в модуле [Resilient](resilient.md).

## Клиент императивный { #client-imperative }

Базовый клиент представлен интерфейсом `HttpClient` и доступен для внедрения из любого модуля транспорта:

```java
public interface HttpClient {

    HttpClientResponse execute(HttpClientRequest request) throws HttpClientException; //(1)!

    default HttpClient with(HttpClientInterceptor interceptor); //(2)!
}
```

1. Выполняет запрос и возвращает ответ; ответ обязательно нужно закрыть
2. Возвращает новое представление `HttpClient` с дополнительным перехватчиком поверх

Ответ держит открытый поток тела, поэтому его нужно закрывать — используйте блок `try`-with-resources:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var request = HttpClientRequest.post("http://localhost:8090/pets/{petId}")
            .pathParam("petId", "1")
            .queryParam("page", 1)
            .header("token", "12345")
            .body(HttpBody.plaintext("refresh"))
            .build();

    try (var response = httpClient.execute(request)) {
        var code = response.code();
        var body = new String(response.body().asInputStream().readAllBytes(), StandardCharsets.UTF_8);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val request = HttpClientRequest.post("http://localhost:8090/pets/{petId}")
        .pathParam("petId", "1")
        .queryParam("page", 1)
        .header("token", "12345")
        .body(HttpBody.plaintext("refresh"))
        .build()

    httpClient.execute(request).use { response ->
        val code = response.code()
        val body = String(response.body().asInputStream().readAllBytes(), StandardCharsets.UTF_8)
    }
    ```

### Построитель запроса { #request-builder }

`HttpClientRequestBuilder` позволяет собирать HTTP-запросы вручную и создаётся через `HttpClientRequest.of(method, uri)`. Построитель создается одним из фабричных методов
`HttpClientRequest` — `get`, `head`, `post`, `put`, `delete`, `connect`, `options`, `trace`, `patch`
или `of(method, uriTemplate)`, — а готовый запрос можно превратить обратно в построитель через `request.toBuilder()`.

| Метод | Описание |
|---|---|
| `pathParam(String name, String \| int \| long \| UUID value)` | Подставляет значение вместо placeholder-а `{name}` в шаблоне URI |
| `queryParam(String name)` | Добавляет параметр запроса без значения |
| `queryParam(String name, String \| int \| long \| boolean \| UUID \| Collection<?> value)` | Добавляет значение параметра запроса |
| `queryParamRemove(String name)` | Удаляет все значения параметра запроса |
| `header(String name, String \| List<String> value)` | Устанавливает заголовок запроса |
| `headerRemove(String name)` | Удаляет заголовок запроса |
| `requestTimeout(Duration \| int millis)` | Переопределяет время ожидания для этого запроса |
| `body(HttpBodyOutput body)` | Устанавливает тело запроса |
| `build()` | Собирает неизменяемый `HttpClientRequest` |

===! ":fontawesome-brands-java: `Java`"

    ```java
    HttpClientRequest request = HttpClientRequest.of("POST", "http://localhost:8090/pets/{petId}")
            .pathParam("petId", "1")
            .queryParam("page", 1)
            .header("token", "12345")
            .requestTimeout(Duration.ofSeconds(5))
            .body(HttpBody.plaintext("refresh"))
            .build();
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val request = HttpClientRequest.of("POST", "http://localhost:8090/pets/{petId}")
        .pathParam("petId", "1")
        .queryParam("page", 1)
        .header("token", "12345")
        .requestTimeout(Duration.ofSeconds(5))
        .body(HttpBody.plaintext("refresh"))
        .build()
    ```

У собранного `HttpClientRequest` доступны `method()`, `uri()`, `uriTemplate()`, `headers()`, `body()` и `requestTimeout()`.
Именно `uriTemplate()` телеметрия использует как имя операции — поэтому шаблонные пути удерживают низкую кардинальность метрик и трассировок.

### Построитель URI { #uri-query-builder }

`UriQueryBuilder` — низкоуровневый помощник, которым сгенерированные декларативные клиенты собирают строку запроса.
Он добавляет параметры по порядку и сам расставляет разделители `?` и `&`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var query = new UriQueryBuilder(true, false); //(1)!
    query.add("page", "1"); //(2)!
    query.add("sort", "name age"); //(3)!
    query.add("debug"); //(4)!

    String uri = "/api/users" + query.build();
    // /api/users?page=1&sort=name+age&debug
    ```

    1. Первый аргумент: начинать строку с `?`; второй: начинать с `&`, если базовый путь уже заканчивается параметром запроса
    2. Добавляет пару `name=value`, обе части кодируются в URL
    3. Значения кодируются в URL, поэтому пробел превращается в `+`
    4. Добавляет параметр без значения

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val query = UriQueryBuilder(true, false) //(1)!
    query.add("page", "1") //(2)!
    query.add("sort", "name age") //(3)!
    query.add("debug") //(4)!

    val uri = "/api/users" + query.build()
    // /api/users?page=1&sort=name+age&debug
    ```

    1. Первый аргумент: начинать строку с `?`; второй: начинать с `&`, если базовый путь уже заканчивается параметром запроса
    2. Добавляет пару `name=value`, обе части кодируются в URL
    3. Значения кодируются в URL, поэтому пробел превращается в `+`
    4. Добавляет параметр без значения

### Тело ответа { #http-body-input }

`HttpBodyInput` описывает тело ответа. Он наследует `HttpBody` и является `Closeable`.

| Метод | Возвращает | Описание |
|--------|---------|-------------|
| `asInputStream()` | `InputStream` | Читает тело как поток |
| `getFullContentIfAvailable()` | `ByteBuffer` | Возвращает тело целиком, если оно уже буферизовано, иначе `null` |
| `contentLength()` | `long` | Длина тела, `-1` если неизвестна |
| `contentType()` | `String` | Значение заголовка `Content-Type`, может быть `null` |
| `close()` | `void` | Освобождает ресурсы соединения |

Исходящий аналог — `HttpBodyOutput`, который создается через `HttpBody.plaintext(...)`, `HttpBody.json(...)`,
`HttpBody.octetStream(...)`, `HttpBody.of(contentType, content)` либо `HttpBodyOutput.of(contentType, inputStream)`
для потоковой передачи тела, которое не помещается в память целиком.

### Ответ клиента { #http-client-response }

`HttpClientResponse` — интерфейс, представляющий HTTP-ответ от сервера. Он является `Closeable`.

| Метод | Возвращает | Описание |
|--------|---------|-------------|
| `code()` | `int` | Код статуса HTTP (200, 404, 500 и т.д.) |
| `headers()` | `HttpHeaders` | Заголовки ответа |
| `body()` | `HttpBodyInput` | Тело ответа |
| `close()` | `void` | Закрывает ответ и освобождает соединение |

### Заголовки { #http-headers-imperative }

`HttpHeaders` дает доступ к заголовкам запроса и ответа. Имена заголовков приводятся к нижнему регистру, поиск регистронезависимый.

| Метод | Возвращает | Описание |
|--------|---------|-------------|
| `getFirst(String name)` | `String` | Первое значение заголовка либо `null` |
| `getAll(String name)` | `List<String>` | Все значения заголовка либо `null` |
| `has(String name)` | `boolean` | Присутствует ли заголовок |
| `names()` | `Set<String>` | Все имена заголовков |
| `size()` | `int` | Количество заголовков |
| `isEmpty()` | `boolean` | Пуст ли набор заголовков |
| `toMutable()` | `MutableHttpHeaders` | Изменяемая копия |

**Чтение заголовков:**

===! ":fontawesome-brands-java: `Java`"

    ```java
    var request = HttpClientRequest.get("http://localhost:8090/api/data").build();

    try (var response = httpClient.execute(request)) {
        HttpHeaders headers = response.headers();
        String contentType = headers.getFirst("content-type");
        List<String> allValues = headers.getAll("x-custom-header");
        boolean hasHeader = headers.has("authorization");
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val request = HttpClientRequest.get("http://localhost:8090/api/data").build()

    httpClient.execute(request).use { response ->
        val headers = response.headers()
        val contentType = headers.getFirst("content-type")
        val allValues = headers.getAll("x-custom-header")
        val hasHeader = headers.has("authorization")
    }
    ```

**Сборка заголовков:**

`HttpHeaders.of(...)` возвращает `MutableHttpHeaders`, который поддерживает `set`, `add` и `remove`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    MutableHttpHeaders headers = HttpHeaders.of();
    headers.add("authorization", "Bearer token123");
    headers.add("x-custom-header", "value");
    headers.set("content-type", "application/json");

    var request = HttpClientRequest.post("http://localhost:8090/api/data")
            .header("authorization", headers.getFirst("authorization"))
            .body(HttpBody.json("{}"))
            .build();
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val headers = HttpHeaders.of()
    headers.add("authorization", "Bearer token123")
    headers.add("x-custom-header", "value")
    headers.set("content-type", "application/json")

    val request = HttpClientRequest.post("http://localhost:8090/api/data")
        .header("authorization", headers.getFirst("authorization")!!)
        .body(HttpBody.json("{}"))
        .build()
    ```

Готовый объект `HttpHeaders` можно также передать прямо в декларативный метод через `@Header`, смотрите [Заголовок](#header).

### Cookies { #cookies-imperative }

Куки — это обычные заголовки: исходящая кука это заголовок `Cookie`, входящая — заголовок `Set-Cookie`.
`Cookie` описывает одну куку, а `Cookies` — служебный класс, который их разбирает и формирует.

**Отправка куки:**

===! ":fontawesome-brands-java: `Java`"

    ```java
    var request = HttpClientRequest.get("http://localhost:8090/api/profile")
            .header("Cookie", Cookie.of("SESSIONID", "12345").toValue())
            .build();
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val request = HttpClientRequest.get("http://localhost:8090/api/profile")
        .header("Cookie", Cookie.of("SESSIONID", "12345").toValue())
        .build()
    ```

**Чтение кук из ответа:**

===! ":fontawesome-brands-java: `Java`"

    ```java
    try (var response = httpClient.execute(request)) {
        var setCookies = response.headers().getAll("set-cookie");
        if (setCookies != null) {
            for (var header : setCookies) {
                Cookie cookie = Cookies.parseSetCookieHeader(header);
                String name = cookie.name();
                String value = cookie.value();
                String domain = cookie.domain();
                String path = cookie.path();
            }
        }
    }
    ```

    1. Имена заголовков сопоставляются без учёта регистра

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    httpClient.execute(request).use { response ->
        val setCookies = response.headers().getAll("set-cookie")
        if (setCookies != null) {
            for (header in setCookies) {
                val cookie = Cookies.parseSetCookieHeader(header)
                val name = cookie.name()
                val value = cookie.value()
                val domain = cookie.domain()
                val path = cookie.path()
            }
        }
    }
    ```

Для декларативного клиента вместо ручной сборки заголовка используйте аннотацию параметра [`@Cookie`](#cookie).

## Телеметрия { #telemetry }

Телеметрия HTTP-клиента устанавливается как перехватчик: `DeclarativeHttpClientConfig` запрашивает у `HttpClientTelemetryFactory`
объект `HttpClientTelemetry` для каждого метода клиента и оборачивает транспорт в `TelemetryInterceptor`.
Точки расширения находятся в пакете `io.koraframework.http.client.common.telemetry`.

Для каждого HTTP-запроса `HttpClientTelemetry.observe(request)` создает `HttpClientObservation`,
который видит запрос через `observeRequest`, ответ через `observeResponse`, сбой через `observeError`
и всегда закрывается вызовом `end()`.

Фабрика по умолчанию `DefaultHttpClientTelemetryFactory` объединяет три опциональные части, каждую из которых можно заменить,
объявив компонент соответствующего типа:

- `DefaultHttpClientLoggerFactory` создает логгеры запроса и ответа;
- `DefaultHttpClientMetricsFactory` создает сборщик метрик;
- `DefaultHttpClientBodyConverter` превращает захваченное тело в строку, которая пишется в лог.

Если для клиента выключены и логирование, и метрики, и трассировка, фабрика возвращает пустую телеметрию и обертка вообще не устанавливается.

**Логирование.** На каждый метод клиента создаются два логгера, названные по классу клиента, методу и направлению:
`com.example.SomeClient.hello.request` и `com.example.SomeClient.hello.response`.
Их уровень определяет объем записи: `INFO` пишет только операцию, `DEBUG` добавляет параметры запроса и заголовки,
`TRACE` добавляет тело. Скрываемые параметры и заголовки заменяются настроенной маской `mask`,
а тело больше `maxRequestBodyLogSize` / `maxResponseBodyLogSize` пропускается с предупреждением.
Настройка самих логгеров описана в разделе [Логирование](logging-slf4j.md).

**Метрики.** Сборщик по умолчанию пишет таймер `http.client.request.duration` с корзинами SLO из
`telemetry.metrics.slo`, размеченный методом HTTP, кодом статуса, маршрутом, адресом сервера и типом ошибки.
Смотрите [Описание метрик](metrics.md#http-client).

**Трассировка.** На каждый запрос создается span с именем `<METHOD> <шаблон пути>` и семантическими атрибутами HTTP
из OpenTelemetry; `telemetry.tracing.pathFull` выбирает между атрибутами `url.full` и `url.path`.
Смотрите [Трассировка](tracing.md).

### Логирование { #telemetry-logging }

Логирование клиента пишется через `SLF4J` под двумя логгерами, названными по имени клиента: `<clientName>.request` и `<clientName>.response`
(где `<clientName>` выводится из интерфейса `@HttpClient`). Включение логирования в конфигурации (`telemetry.logging.enabled = true`) активирует
телеметрию, но **что именно** пишется, определяется уровнем логирования этих логгеров, поэтому детализацией вы управляете из вашего фреймворка логирования (`logback` и т.д.):

| Уровень лога | Что логируется |
|--------------|----------------|
| `INFO`  | Строка начала запроса и конца ответа: метод, шаблон пути, статус ответа, код результата и длительность |
| `DEBUG` | Дополнительно **заголовки** запроса и ответа |
| `TRACE` | Дополнительно **тела** запроса и ответа, а также полный (нешаблонизированный) путь |

Поля конфигурации формируют вывод (полный список см. в [Конфигурации](#configuration)):

* `pathTemplate` — при `true` (по умолчанию) логируется шаблон маршрута с низкой кардинальностью (`/users/{id}`) и используется как метка метрик/трассировки вместо разрешённого пути (`/users/42`); на `TRACE` логируется разрешённый путь
* `maskHeaders` — имена заголовков, значения которых заменяются на `mask` (по умолчанию маскируются `authorization`, `cookie`, `set-cookie`)
* `maskQueries` — имена query-параметров, значения которых заменяются на `mask`
* `mask` — строка замены (по умолчанию `***`)

Для клиента, имя которого выводится как `someClient`, включить полное логирование тел можно так:

```xml
<logger name="someClient.request" level="TRACE"/>
<logger name="someClient.response" level="TRACE"/>
```

### Свой логгер { #telemetry-custom-logger }

Чтобы полностью управлять форматом или назначением лога, предоставьте свой компонент `HttpClientLoggerFactory` (или `HttpClientLogger`) — он заменит
фабрику по умолчанию `Sl4fjHttpClientLoggerFactory`. То же касается метрик (`HttpClientMetricsFactory`) и трассировки (`HttpClientTracerFactory`):
предоставление любого из этих компонентов переопределяет соответствующую реализацию по умолчанию, остальные сохраняют реализацию по умолчанию.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class MyHttpClientLoggerFactory implements HttpClientLoggerFactory {

        @Override
        public HttpClientLogger get(TelemetryConfig.LogConfig logging, String clientName) {
            return new MyHttpClientLogger(clientName); //(1)!
        }
    }
    ```

    1. Ваша реализация `HttpClientLogger`, управляющая тем, что и как логировать

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class MyHttpClientLoggerFactory : HttpClientLoggerFactory {

        override fun get(logging: TelemetryConfig.LogConfig, clientName: String): HttpClientLogger {
            return MyHttpClientLogger(clientName) //(1)!
        }
    }
    ```

    1. Ваша реализация `HttpClientLogger`, управляющая тем, что и как логировать
