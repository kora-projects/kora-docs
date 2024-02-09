Модуль предоставляет тонкий слой абстракции над библиотеками HTTP-клиентов для создания HTTP-клиентов с помощью аннотаций
с помощью аннотаций в декларативном стиле, так и в императивном стиле.

## AsyncHttpClient

Реализация HTTP клиента основанная на библиотеке [Async HTTP Client](https://github.com/AsyncHttpClient/async-http-client).

### Подключение

=== ":fontawesome-brands-java: `Java`"

    Зависимость `build.gradle`:
    ```groovy
    annotationProcessor "ru.tinkoff.kora:annotation-processors"
    implementation "ru.tinkoff.kora:http-client-async"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends AsyncHttpClientModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    Зависимость `build.gradle.kts`:
    ```groovy
    ksp("ru.tinkoff.kora:symbol-processors")
    implementation("ru.tinkoff.kora:http-client-async")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : AsyncHttpClientModule
    ```

### Конфигурация

Конфигурация отвечает за общие настройки реализации HTTP клиента.
Пример конфигурации описанной в классе `HttpClientConfig`:

===! ":material-code-json: `Hocon`"

    ```javascript
    httpClient {
        connectTimeout = "5s" //(1)!
        readTimeout = "2m" //(2)!
        useEnvProxy = false //(3)!
        proxy {
            host = "localhost"  //(4)!
            port = 8090  //(5)!
            user = "user"  //(6)!
            password = "password"  //(7)!
            nonProxyHosts = [ "host1", "host2" ]  //(8)!
        }
    }
    ```

    1.  Максимальное время на установление соединения
    2.  Максимальное время на чтение ответа
    3.  Использовать ли переменные окружения для настройки прокси
    4.  Адрес прокси
    5.  Порт прокси
    6.  Пользователь для прокси
    7.  Пароль для прокси
    8.  Хосты которые следует исключить из проксирования

=== ":simple-yaml: `YAML`"

    ```yaml
    httpClient:
      connectTimeout: "5s" #(1)!
      readTimeout: "2m" #(2)!
      useEnvProxy: false #(3)!
      proxy:
        host: "localhost"  #(4)!
        port: 8090  #(5)!
        user: "user"  #(6)!
        password: "password"  #(7)!
        nonProxyHosts: [ "host1", "host2" ]  #(8)!
    ```

    1.  Максимальное время на установление соединения
    2.  Максимальное время на чтение ответа
    3.  Использовать ли переменные окружения для настройки прокси
    4.  Адрес прокси
    5.  Порт прокси
    6.  Пользователь для прокси
    7.  Пароль для прокси
    8.  Хосты которые следует исключить из проксирования

## OkHttp

Реализация HTTP клиента основанная на библиотеке [OkHttp](https://github.com/square/okhttp).
Учитывайте что реализация написана на Kotlin и использует соответствующие зависимости.

### Подключение

=== ":fontawesome-brands-java: `Java`"

    Зависимость `build.gradle`:
    ```groovy
    annotationProcessor "ru.tinkoff.kora:annotation-processors"
    implementation "ru.tinkoff.kora:http-client-ok"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends OkHttpClientModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    Зависимость `build.gradle.kts`:
    ```groovy
    ksp("ru.tinkoff.kora:symbol-processors")
    implementation("ru.tinkoff.kora:http-client-ok")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : OkHttpClientModule
    ```

### Конфигурация

Конфигурация отвечает за общие настройки реализации HTTP клиента.
Пример конфигурации описанной в классах `OkHttpClientConfig` и `HttpClientConfig`:

===! ":material-code-json: `Hocon`"

    ```javascript
    httpClient {
        ok {
            followRedirects = true //(1)!
        }
        connectTimeout = "5s" //(2)!
        readTimeout = "2m" //(3)!
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

    1.  Следовать ли по [перенаправлениям в HTTP](https://developer.mozilla.org/ru/docs/Web/HTTP/Redirections)
    2.  Максимальное время на установление соединения
    3.  Максимальное время на чтение ответа
    4.  Использовать ли переменные окружения для настройки прокси
    5.  Адрес прокси
    6.  Порт прокси
    7.  Пользователь для прокси
    8.  Пароль для прокси
    9.  Хосты которые следует исключить из проксирования

=== ":simple-yaml: `YAML`"

    ```yaml
    httpClient:
      ok:
        followRedirects: true #(1)!
      connectTimeout: "5s" #(2)!
      readTimeout: "2m" #(3)!
      useEnvProxy: false #(4)!
      proxy:
        host: "localhost" #(5)!
        port: 8090  #(6)!
        user: "user"  #(7)!
        password: "password" #(8)!
        nonProxyHosts: [ "host1", "host2" ] #(9)!
    ```

    1.  Следовать ли по [перенаправлениям в HTTP](https://developer.mozilla.org/ru/docs/Web/HTTP/Redirections)
    2.  Максимальное время на установление соединения
    3.  Максимальное время на чтение ответа
    4.  Использовать ли переменные окружения для настройки прокси
    5.  Адрес прокси
    6.  Порт прокси
    7.  Пользователь для прокси
    8.  Пароль для прокси
    9.  Хосты которые следует исключить из проксирования

## Нативный клиент

Реализация HTTP клиента на основании нативного клиента поставляемого в [JDK](https://openjdk.org/groups/net/httpclient/intro.html).

### Подключение

=== ":fontawesome-brands-java: `Java`"

    Зависимость `build.gradle`:
    ```groovy
    annotationProcessor "ru.tinkoff.kora:annotation-processors"
    implementation "ru.tinkoff.kora:http-client-jdk"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends JdkHttpClientModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    Зависимость `build.gradle.kts`:
    ```groovy
    ksp("ru.tinkoff.kora:symbol-processors")
    implementation("ru.tinkoff.kora:http-client-jdk")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : JdkHttpClientModule
    ```

### Конфигурация

Конфигурация отвечает за общие настройки реализации HTTP клиента.
Пример конфигурации описанной в классе `JdkHttpClientConfig` и `HttpClientConfig`:

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

    1.  Количество потоков для HTTP клиента
    2.  Какую версию HTTP протокола использовать (доступны `HTTP_2` / `HTTP_1_1`)
    3.  Максимальное время на установление соединения
    4.  Использовать ли переменные окружения для настройки прокси
    5.  Адрес прокси
    6.  Порт прокси
    7.  Пользователь для прокси
    8.  Пароль для прокси
    9.  Хосты которые следует исключить из проксирования

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

    1.  Количество потоков для HTTP клиента
    2.  Какую версию HTTP протокола использовать (доступны `HTTP_2` / `HTTP_1_1`)
    3.  Максимальное время на установление соединения
    4.  Использовать ли переменные окружения для настройки прокси
    5.  Адрес прокси
    6.  Порт прокси
    7.  Пользователь для прокси
    8.  Пароль для прокси
    9.  Хосты которые следует исключить из проксирования

## Клиент декларативный

Предлагается использовать специальные аннотации для создания декларативного клиента:

* `@HttpClient` — указывает что интерфейс является декларативным HTTP клиентом
* `@HttpRoute` — указывает [тип HTTP запроса](https://developer.mozilla.org/ru/docs/Web/HTTP/Methods) и путь запроса

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

### Конфигурация клиента

Конфигурация конкретной реализации `@HttpClient` по умолчанию для поиска конфигурации использует следующий путь `httpClient.{имя класса в нижнем регистре}`,
либо указывается в параметре `configPath` в аннотации:

=== ":fontawesome-brands-java: `Java`"

    ```java
    @HttpClient(configPath = "path.to.config") //(1)!
    public interface SomeClient {

        @HttpRoute(method = HttpMethod.GET, path = "/hello/world")
        void hello();
    }
    ```

    1. Путь до конфигурации конкретно этого клиента

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpClient(configPath = "path.to.config") //(1)!
    interface SomeClient {

        @HttpRoute(method = HttpMethod.GET, path = "/hello/world")
        fun hello()
    }
    ```

    1. Путь до конфигурации конкретно этого клиента

Пример конфигурации в случае пути `path.to.config` описанной в классе `DeclarativeHttpClientConfig`:

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

    1.  URL сервиса куда будут отправляться запросы
    2.  Максимальное время запроса
    3.  Включает логгирование модуля
    4.  Включает метрики модуля
    5.  Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) метрики
    6.  Включает трассировку модуля

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

    1.  URL сервиса куда будут отправляться запросы
    2.  Максимальное время запроса
    3.  Включает логгирование модуля
    4.  Включает метрики модуля
    5.  Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) метрики
    6.  Включает трассировку модуля

### Конфигурация метода

На примере выше рассмотренного HTTP клиента, можно настроить отдельно часть параметров для определенного метода, путь к конфигурации 
определяется путем к клиенту и именем метода, в примере выше конфигурация `path.to.config` 
и метода `hello` финальный путь будет `path.to.config.getHello`

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

    1.  Максимальное время запроса метода
    2.  Включает логгирование модуля
    3.  Включает метрики модуля
    4.  Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) метрики
    5.  Включает трассировку модуля

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

    1.  Максимальное время запроса метода
    2.  Включает логгирование модуля
    3.  Включает метрики модуля
    4.  Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) метрики
    5.  Включает трассировку модуля

### Запрос

Секция описывает преобразования HTTP запроса у декларативного HTTP клиента.
Предлагается использовать специальные аннотации для указания параметров запроса.

#### Параметр пути

`@Path` — обозначает значение части пути запроса, сам параметр указывается в `{ковычка}` в пути 
и имя параметра указывается в `value` либо по умолчанию равно имени аргумента метода.

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

#### Параметр запроса

`@Query` — значение параметра запроса, имя параметра указывается в `value` либо по умолчанию равно имени аргумента метода.

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

Можно отправлять параметры запроса в формате ключ и значение, для этого предполагается использовать тип `Map`,
где ключом является имя параметра и обязано иметь тип `String`, а значение параметра может быть любым типом и будет обработано через `String.valueOf()`:

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

#### Заголовок

`@Header` — значение [заголовка запроса](https://developer.mozilla.org/ru/docs/Web/HTTP/Headers), имя параметра указывается в `value` либо по умолчанию равно имени аргумента метода.

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

Можно отправлять параметры запроса в формате ключ и значение, для этого предполагается использовать `HttpHeaders` тип либо тип `Map`,
где ключом является имя параметра и обязано иметь тип `String`, а значение параметра может быть любым типом и будет обработано через `String.valueOf()`:

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

#### Тело запроса

Для указания тела запроса требуется использовать аргумент метода без специальных аннотации, 
по умолчанию поддерживаются такие типы как `byte[]`, `ByteBuffer` или `String`.

##### Json 

Для указания, что тело является Json и ему требуется автоматически создать такого писателя и внедрить его,
требуется использовать аннотацию `@Json`:

=== ":fontawesome-brands-java: `Java`"

    ```java
    @HttpClient
    public interface SomeClient {

        record MyBody(String name) { }

        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        void hello(@Json MyBody body); //(1)!
    }
    ```

    1. Указывает что тело должно быть записано как Json

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpClient
    interface SomeClient {

        data class MyBody(val name: String) { }

        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        fun hello(@Json body: MyBody) //(1)!
    }
    ```

    1. Указывает что тело должно быть записано как Json

Требуется подключить модуль [Json](json.md).

##### Текстовая форма

Можно использовать `FormUrlEncoded` как тип аргумента тела [форма данных](https://www.w3.org/TR/html401/interact/forms.html#h-17.13.4.1).

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

Пример вызова метода с такой формой будет выглядеть так:

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

##### Бинарная форма

Можно использовать `FormMultipart` как тип аргумента тела [бинарная форма](https://www.w3.org/TR/html401/interact/forms.html#h-17.13.4.2).

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

Пример вызова метода с такой формой будет выглядеть так:

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

##### Самописное

Если тело требуется записывать отличным от стандартных механизмов способом,
то можно использовать специальный интерфейс `HttpClientRequestMapper` для реализации собственной логики:

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

#### Куки

`@Cookie` — значение [Cookie](https://developer.mozilla.org/ru/docs/Glossary/Cookie), имя параметра указывается в `value` либо по умолчанию равно имени аргумента метода.

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

#### Обязательные параметры

=== ":fontawesome-brands-java: `Java`"

    По умолчанию все аргументы объявленные в методе являются **обязательными** (*NotNull*).

=== ":simple-kotlin: `Kotlin`"

    По умолчанию все аргументы объявленные в методе которые не используют [Kotlin Nullability](https://kotlinlang.ru/docs/null-safety.html) синтаксис считаются **обязательными** (*NotNull*).

#### Необязательные параметры

=== ":fontawesome-brands-java: `Java`"

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

### Ответ

Секция описывает преобразование HTTP ответа от декларативного HTTP клиента.

#### Тело ответа

По умолчанию можно использовать стандартные типы возвращаемых значений тела ответа, такие как `void`, `byte[]`, `ByteBuffer` либо `String`.

##### Json

Если предполагается читать тело как Json, то требуется использовать аннотацию `@Json` над методом.

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

    1. Указывает что ответ должен быть прочитан как Json

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

    1. Указывает что ответ должен быть прочитан как Json

Требуется подключить модуль [Json](json.md).

##### Сущность ответа

Если предполагается читать тело и получить также заголовки и статус код ответа, 
то предполагается использовать `HttpResponseEntity`, это обертка над телом ответа.

Ниже показан пример аналогичный примеру Json вместе с оберткой `HttpResponseEntity`:

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

##### Самописное

Если требуется чтение ответа отличным способом, то можно использовать специальный интерфейс `HttpClientResponseMapper`:

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

#### Ошибка ответа

По умолчанию преобразование будет применяться только для `2хх` HTTP статусов кодов,
для всех остальных будет выбрасываться исключение `HttpClientResponseException`, которое содержит [HTTP статус код](https://developer.mozilla.org/ru/docs/Web/HTTP/Status), тело ответа и заголовки ответа.

#### Преобразование по коду

Если требуются специфичные преобразование в зависимости от [HTTP статус кода](https://developer.mozilla.org/ru/docs/Web/HTTP/Status) ответа, можно использовать аннотацию `@ResponseCodeMapper` для указания
соответствия HTTP статус кода и преобразователя `HttpClientResponseMapper`.

Также можно использовать `ResponseCodeMapper.DEFAULT` как указание поведения по умолчанию для всех не перечисленных статус кодов.

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

В примере выше для статуса кода `200` будет использовать `ResponseSuccessMapper`, 
а для всех остальных статус кодов будет использован `ResponseErrorMapper`.

### Сигнатуры

Доступные сигнатуры для методов декларативного HTTP клиента из коробки:

=== ":fontawesome-brands-java: `Java`"

    Под `T` подразумевается тип возвращаемого значения, либо `Void`.

    - `T myMethod()`
    - `CompletionStage<T> myMethod()` [CompletionStage](https://docs.oracle.com/javase/8/docs/api/java/util/concurrent/CompletionStage.html)
    - `Mono<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/)

=== ":simple-kotlin: `Kotlin`"

    Под `T` подразумевается тип возвращаемого значения, либо `Unit`.

    - `myMethod(): T`
    - `suspend myMethod(): T` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine)

## Перехватчики

Можно создавать перехватчики для изменения поведения либо создания дополнительного поведения используя класс `HttpClientInterceptor`.
Перехватчики можно накладывать на конкретные методы либо весь `@HttpClient` класс целиком:

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

## Клиент императивный

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
