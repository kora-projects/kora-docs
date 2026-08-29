---
description: "Explains the two independent Kora S3 artifacts: the declarative s3-client-kora client built on Kora's own HTTP client and the s3-client-aws wrapper that publishes the AWS SDK S3Client. Covers @S3.Client, @S3.Bucket, @S3.Get, @S3.Head, @S3.List, @S3.Put, @S3.Delete, request arguments, response models, configuration, exceptions and testing."
agent:
  use_when: "Use this file for Kora docs or implementation questions about S3-compatible object storage: choosing between s3-client-kora and s3-client-aws, declarative clients, bucket and credentials resolution, key templates, multipart upload, byte ranges and exception handling; key triggers include @S3.Client, @S3.Bucket, @S3.Get, @S3.Head, @S3.List, @S3.Put, @S3.Delete, KoraS3ClientModule, AwsS3ClientModule, S3ClientConfig, AwsS3Config, S3ClientFactory, GetObjectResult, HeadObjectResult, ListBucketResult, S3ClientNoSuchKeyException."
---

Kora предоставляет **два независимых артефакта для S3**. Общего у них только протокол: разные
координаты Maven, разные пакеты, разные секции конфигурации, разные API.
Выберите тот, который соответствует желаемому способу работы с [S3-совместимым объектным хранилищем](https://aws.amazon.com/s3/faqs/),
либо подключите оба, если нужны оба.

| Артефакт                                        | Что предоставляет                                                                                                            | Когда использовать                                                                            |
|-------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| `io.koraframework.experimental:s3-client-kora`  | Декларативные интерфейсы `@S3.Client` и императивный контракт `S3Client`, реализованные поверх собственного HTTP-клиента Kora | Нужны сгенерированные на этапе компиляции клиенты с телеметрией для операций над объектами     |
| `io.koraframework:s3-client-aws`                | Клиент AWS SDK `software.amazon.awssdk.services.s3.S3Client`, опубликованный как компонент графа                             | Нужна вся поверхность AWS SDK: администрирование бакетов, копирование, предподписанные URL, ACL |

!!! warning "Два разных типа `S3Client`"

    Оба артефакта предоставляют тип с именем `S3Client`, и они никак не связаны:
    `io.koraframework.s3.client.kora.S3Client` — это императивный контракт Kora, а
    `software.amazon.awssdk.services.s3.S3Client` — клиент AWS SDK. Импортируйте нужный —
    их путаница приводит к непонятным ошибкам сборки графа «no factory found».

Если в classpath оказался не тот артефакт, компиляция падает с сообщениями вида
`package S3 does not exist` или `package io.koraframework.s3.client.model does not exist`:
аннотации `@S3` и все типы моделей есть только в `s3-client-kora`.

Если нужен пошаговый разбор перед справочным описанием, смотрите [S3](../guides/s3.md).

## Kora клиент { #kora }

??? warning "Экспериментальный модуль"

    **Экспериментальный** модуль полностью работает и протестирован, но требует дополнительной апробации и аналитики использования,
    поэтому API потенциально может претерпеть незначительные изменения до того, как станет полностью стабильным.

Артефакт `s3-client-kora` реализует REST API `S3` напрямую поверх собственного [HTTP-клиента](http-client.md) Kora.
Он предоставляет декларативные интерфейсы `@S3.Client`, императивный контракт `S3Client`, модели запросов/ответов
и телеметрию. От AWS SDK он **не** зависит.

### Подключение { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "io.koraframework.experimental:s3-client-kora"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends KoraS3ClientModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("io.koraframework.experimental:s3-client-kora")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : KoraS3ClientModule
    ```

Требуется добавить любой модуль [HTTP-клиента](http-client.md), поскольку `S3`-клиент выполняет запросы
через компонент `HttpClient` из графа — например
[Apache HttpClient](http-client.md#apache-httpclient), [OkHttp](http-client.md#okhttp)
или [нативный JDK-клиент](http-client.md#native-client).

### Конфигурация { #configuration }

Каждый декларативный клиент читает собственную конфигурацию `S3ClientConfig` по пути, объявленному в
[`@S3.Client`](#client-configuration). Основные параметры:

===! ":material-code-json: `Hocon`"

    ```javascript
    s3client.someClient {
        endpoint = "http://localhost:9000" //(1)!
        credentials {
            accessKey = "someKey" //(2)!
            secretKey = "someSecret" //(3)!
        }
        region = "aws-global" //(4)!
    }
    ```

    1.  Адрес (`URL`) хранилища `S3` (`обязательный`, по умолчанию не указано)
    2.  Ключ доступа к `S3` (`обязательный`, если не каждый метод клиента принимает аргумент [`S3Credentials`](#credentials))
    3.  Секрет доступа к `S3` (`обязательный`, если не каждый метод клиента принимает аргумент [`S3Credentials`](#credentials))
    4.  Регион хранилища `S3` (по умолчанию: `aws-global`)

=== ":simple-yaml: `YAML`"

    ```yaml
    s3client:
      someClient:
        endpoint: "http://localhost:9000" #(1)!
        credentials:
          accessKey: "someKey" #(2)!
          secretKey: "someSecret" #(3)!
        region: "aws-global" #(4)!
    ```

    1.  Адрес (`URL`) хранилища `S3` (`обязательный`, по умолчанию не указано)
    2.  Ключ доступа к `S3` (`обязательный`, если не каждый метод клиента принимает аргумент [`S3Credentials`](#credentials))
    3.  Секрет доступа к `S3` (`обязательный`, если не каждый метод клиента принимает аргумент [`S3Credentials`](#credentials))
    4.  Регион хранилища `S3` (по умолчанию: `aws-global`)

??? note "Полная конфигурация"

    Полная конфигурация описана в классах `S3ClientConfig` и `S3ClientConfigWithCredentials`
    (указаны примеры значений или значения по умолчанию):

    ===! ":material-code-json: `Hocon`"

        ```javascript
        s3client.someClient {
            endpoint = "http://localhost:9000" //(1)!
            credentials {
                accessKey = "someKey" //(2)!
                secretKey = "someSecret" //(3)!
            }
            region = "aws-global" //(4)!
            addressStyle = "PATH" //(5)!
            requestTimeout = "45s" //(6)!
            upload {
                partSize = "5MiB" //(7)!
                chunkSize = "64KiB" //(8)!
                singlePartUploadLimit = "100MiB" //(9)!
            }
            telemetry {
                logging {
                    enabled = false //(10)!
                }
                metrics {
                    enabled = false //(11)!
                    slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(12)!
                    tags = { // (13)!
                        "key1" = "value1"
                        "key2" = "value2"
                    }
                }
                tracing {
                    enabled = true //(14)!
                    attributes = { // (15)!
                        "key1" = "value1"
                        "key2" = "value2"
                    }
                }
            }
        }
        ```

        1.  Адрес (`URL`) хранилища `S3` (`обязательный`, по умолчанию не указано)
        2.  Ключ доступа к `S3` (`обязательный`, если не каждый метод клиента принимает аргумент [`S3Credentials`](#credentials))
        3.  Секрет доступа к `S3` (`обязательный`, если не каждый метод клиента принимает аргумент [`S3Credentials`](#credentials))
        4.  Регион хранилища `S3`, используется при подписании запросов (по умолчанию: `aws-global`)
        5.  Стиль доступа к объектам, может иметь значения `PATH` или `VIRTUAL_HOSTED` (по умолчанию: `PATH`)
        6.  Максимальное время выполнения операции, передаётся в нижележащий `HTTP`-запрос (по умолчанию: `45s`)
        7.  Размер части при [многочастной загрузке](#multipart-upload) тела типа `InputStream` (по умолчанию: `5MiB`)
        8.  Размер чанка кодирования `aws-chunked`, когда телом является [`ContentWriter`](#file-body) (по умолчанию: `64KiB`)
        9.  Размер объекта, начиная с которого многочастная загрузка предпочтительнее загрузки одним запросом (по умолчанию: `100MiB`)
        10. Включает логирование модуля (по умолчанию: `false`)
        11. Включает метрики модуля (по умолчанию: `false`)
        12. Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
        13. Настройка тегов метрик (по умолчанию: `{}`)
        14. Включает трассировку модуля (по умолчанию: `true`)
        15. Настройка атрибутов трассировки (по умолчанию: `{}`)

    === ":simple-yaml: `YAML`"

        ```yaml
        s3client:
          someClient:
            endpoint: "http://localhost:9000" #(1)!
            credentials:
              accessKey: "someKey" #(2)!
              secretKey: "someSecret" #(3)!
            region: "aws-global" #(4)!
            addressStyle: "PATH" #(5)!
            requestTimeout: "45s" #(6)!
            upload:
              partSize: "5MiB" #(7)!
              chunkSize: "64KiB" #(8)!
              singlePartUploadLimit: "100MiB" #(9)!
            telemetry:
              logging:
                enabled: false #(10)!
              metrics:
                enabled: false #(11)!
                slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(12)!
                tags: #(13)!
                  key1: value1
                  key2: value2
              tracing:
                enabled: true #(14)!
                attributes: #(15)!
                  key1: value1
                  key2: value2
        ```

        1.  Адрес (`URL`) хранилища `S3` (`обязательный`, по умолчанию не указано)
        2.  Ключ доступа к `S3` (`обязательный`, если не каждый метод клиента принимает аргумент [`S3Credentials`](#credentials))
        3.  Секрет доступа к `S3` (`обязательный`, если не каждый метод клиента принимает аргумент [`S3Credentials`](#credentials))
        4.  Регион хранилища `S3`, используется при подписании запросов (по умолчанию: `aws-global`)
        5.  Стиль доступа к объектам, может иметь значения `PATH` или `VIRTUAL_HOSTED` (по умолчанию: `PATH`)
        6.  Максимальное время выполнения операции, передаётся в нижележащий `HTTP`-запрос (по умолчанию: `45s`)
        7.  Размер части при [многочастной загрузке](#multipart-upload) тела типа `InputStream` (по умолчанию: `5MiB`)
        8.  Размер чанка кодирования `aws-chunked`, когда телом является [`ContentWriter`](#file-body) (по умолчанию: `64KiB`)
        9.  Размер объекта, начиная с которого многочастная загрузка предпочтительнее загрузки одним запросом (по умолчанию: `100MiB`)
        10. Включает логирование модуля (по умолчанию: `false`)
        11. Включает метрики модуля (по умолчанию: `false`)
        12. Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
        13. Настройка тегов метрик (по умолчанию: `{}`)
        14. Включает трассировку модуля (по умолчанию: `true`)
        15. Настройка атрибутов трассировки (по умолчанию: `{}`)

Имя бакета (`bucket`) **не** входит в `S3ClientConfig`. Оно определяется отдельно через
[`@S3.Bucket`](#bucket) и может указывать на любой путь конфигурации.

Метрики модуля описаны в разделе [Справочник по метрикам](metrics.md#s3-client).

## Декларативный клиент { #client-declarative }

Для создания декларативного клиента используются специальные аннотации:

* `@S3.Client` — помечает интерфейс как декларативный S3-клиент
* `@S3.Bucket` — объявляет, откуда берётся [имя бакета](#bucket)
* `@S3.Get` — метод выполняет операцию [получения объекта](#get-file)
* `@S3.Head` — метод выполняет операцию [получения метаданных объекта](#metadata)
* `@S3.List` — метод выполняет операцию [получения списка объектов](#list-files)
* `@S3.Put` — метод выполняет операцию [добавления объекта](#add-file)
* `@S3.Delete` — метод выполняет операцию [удаления объекта](#delete-file)

Все аннотации находятся в пакете `io.koraframework.s3.client.kora.annotation`.
На один метод допускается ровно одна аннотация операции.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient")
    @S3.Bucket(".bucket")
    public interface SomeClient {

        @S3.Get
        GetObjectResult operation(String key);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    @S3.Bucket(".bucket")
    interface SomeClient {

        @S3.Get
        fun operation(key: String): GetObjectResult
    }
    ```

`@S3.Client` можно поставить только на интерфейс; классы процессор отклоняет с ошибкой
`@S3.Client can only be applied to an interface`.

### Конфигурация клиента { #client-configuration }

Значение `value` аннотации `@S3.Client` — это путь конфигурации, из которого читается [`S3ClientConfig`](#configuration):

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient") //(1)!
    @S3.Bucket(".bucket")
    public interface SomeClient {

        @S3.Get
        GetObjectResult operation(String key);
    }
    ```

    1. Путь к конфигурации данного конкретного клиента

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient") //(1)!
    @S3.Bucket(".bucket")
    interface SomeClient {

        @S3.Get
        fun operation(key: String): GetObjectResult
    }
    ```

    1. Путь к конфигурации данного конкретного клиента

!!! warning "Путь клиента без значения"

    `@S3.Client` без значения **не** означает «корень конфигурации».
    Процессор подставляет **простое имя интерфейса**, поэтому `@S3.Client` на
    `interface SomeClient` читает конфигурацию по пути `SomeClient`. Всегда указывайте явный путь
    вида `@S3.Client("s3client.someClient")` — так настройки каждого клиента остаются разделены,
    а файл конфигурации — читаемым.

У каждого клиента своя секция конфигурации, поэтому два клиента в одном приложении могут работать
с двумя разными хранилищами:

===! ":material-code-json: `Hocon`"

    ```javascript
    s3client {
        documents {
            endpoint = ${DOCUMENTS_S3_URL}
            bucket = "documents"
            credentials {
                accessKey = ${DOCUMENTS_S3_ACCESS_KEY}
                secretKey = ${DOCUMENTS_S3_SECRET_KEY}
            }
        }

        avatars {
            endpoint = ${AVATARS_S3_URL}
            bucket = "avatars"
            credentials {
                accessKey = ${AVATARS_S3_ACCESS_KEY}
                secretKey = ${AVATARS_S3_SECRET_KEY}
            }
        }
    }
    ```

=== ":simple-yaml: `YAML`"

    ```yaml
    s3client:
      documents:
        endpoint: ${DOCUMENTS_S3_URL}
        bucket: "documents"
        credentials:
          accessKey: ${DOCUMENTS_S3_ACCESS_KEY}
          secretKey: ${DOCUMENTS_S3_SECRET_KEY}

      avatars:
        endpoint: ${AVATARS_S3_URL}
        bucket: "avatars"
        credentials:
          accessKey: ${AVATARS_S3_ACCESS_KEY}
          secretKey: ${AVATARS_S3_SECRET_KEY}
    ```

### Бакет { #bucket }

Имя бакета никогда не берётся из конфигурации клиента неявно — оно всегда объявляется
через `@S3.Bucket`. Есть три способа его задать, они проверяются в таком порядке:

1. Параметр метода с аннотацией `@S3.Bucket` — бакет передаётся во время выполнения
2. `@S3.Bucket("config.path")` на методе — бакет читается из конфигурации для этого метода
3. `@S3.Bucket("config.path")` на интерфейсе — бакет читается из конфигурации для всех методов

Путь, начинающийся с точки, **относителен** пути клиента, объявленного в `@S3.Client`;
путь без ведущей точки — абсолютный путь в конфигурации.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient")
    @S3.Bucket(".bucket") //(1)!
    public interface SomeClient {

        @S3.Get
        GetObjectResult fromDefaultBucket(String key);

        @S3.Get
        @S3.Bucket("s3client.archive.bucket") //(2)!
        GetObjectResult fromArchiveBucket(String key);

        @S3.Get
        GetObjectResult fromRuntimeBucket(@S3.Bucket String bucket, String key); //(3)!
    }
    ```

    1. Относительный путь: разрешается в `s3client.someClient.bucket`
    2. Абсолютный путь: разрешается в `s3client.archive.bucket`
    3. Бакет передаётся во время выполнения; параметр не входит в [ключ объекта](#key-template)

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    @S3.Bucket(".bucket") //(1)!
    interface SomeClient {

        @S3.Get
        fun fromDefaultBucket(key: String): GetObjectResult

        @S3.Get
        @S3.Bucket("s3client.archive.bucket") //(2)!
        fun fromArchiveBucket(key: String): GetObjectResult

        @S3.Get
        fun fromRuntimeBucket(@S3.Bucket bucket: String, key: String): GetObjectResult //(3)!
    }
    ```

    1. Относительный путь: разрешается в `s3client.someClient.bucket`
    2. Абсолютный путь: разрешается в `s3client.archive.bucket`
    3. Бакет передаётся во время выполнения; параметр не входит в [ключ объекта](#key-template)

Конфигурация для примера выше:

===! ":material-code-json: `Hocon`"

    ```javascript
    s3client {
        someClient {
            endpoint = ${S3_URL}
            bucket = "documents" //(1)!
            credentials {
                accessKey = ${S3_ACCESS_KEY}
                secretKey = ${S3_SECRET_KEY}
            }
        }

        archive {
            bucket = "documents-archive" //(2)!
        }
    }
    ```

    1.  Читается аннотацией `@S3.Bucket(".bucket")`
    2.  Читается аннотацией `@S3.Bucket("s3client.archive.bucket")`

=== ":simple-yaml: `YAML`"

    ```yaml
    s3client:
      someClient:
        endpoint: ${S3_URL}
        bucket: "documents" #(1)!
        credentials:
          accessKey: ${S3_ACCESS_KEY}
          secretKey: ${S3_SECRET_KEY}

      archive:
        bucket: "documents-archive" #(2)!
    ```

    1.  Читается аннотацией `@S3.Bucket(".bucket")`
    2.  Читается аннотацией `@S3.Bucket("s3client.archive.bucket")`

!!! warning "Бакет обязателен"

    Метод, у которого нет ни одного источника бакета, падает на этапе компиляции с ошибкой
    `S3 operation '...' has no bucket source`. Аннотация `@S3.Bucket` без значения на типе или методе
    падает с ошибкой `S3 bucket config path is missing`: пустое значение осмысленно только на параметре.

!!! note "Имя бакета генерируется, а не внедряется"

    Имя бакета из конфигурации попадает в сгенерированный класс `$SomeClient_BucketsConfig`, а не в
    внедряемый компонент. Код, которому нужно то же имя бакета в другом месте — например, инициализатор
    бакета — читает тот же путь конфигурации самостоятельно через [`@ConfigSource`](config.md), смотрите
    [Администрирование бакетов](#bucket-administration).

### Учётные данные { #credentials }

По умолчанию учётные данные берутся из секции `credentials` конфигурации клиента.
Метод может вместо этого принимать параметр `S3Credentials` и подписывать им конкретный вызов:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient")
    @S3.Bucket(".bucket")
    public interface SomeClient {

        @S3.Get
        GetObjectResult withConfigCredentials(String key); //(1)!

        @S3.Get
        GetObjectResult withCallCredentials(S3Credentials credentials, String key); //(2)!
    }
    ```

    1. Использует `credentials { accessKey, secretKey }` из конфигурации клиента
    2. Использует учётные данные, переданные во время выполнения; параметр не входит в ключ объекта

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    @S3.Bucket(".bucket")
    interface SomeClient {

        @S3.Get
        fun withConfigCredentials(key: String): GetObjectResult //(1)!

        @S3.Get
        fun withCallCredentials(credentials: S3Credentials, key: String): GetObjectResult //(2)!
    }
    ```

    1. Использует `credentials { accessKey, secretKey }` из конфигурации клиента
    2. Использует учётные данные, переданные во время выполнения; параметр не входит в ключ объекта

Значение `S3Credentials` создаётся статической фабрикой:

===! ":fontawesome-brands-java: `Java`"

    ```java
    S3Credentials credentials = S3Credentials.of("someKey", "someSecret");
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val credentials = S3Credentials.of("someKey", "someSecret")
    ```

Тип конфигурации клиента выбирает процессор: если **каждый** метод интерфейса принимает параметр
`S3Credentials`, клиент привязывается к `S3ClientConfig`, и секция `credentials` не нужна вовсе.
Если хотя бы один метод её не принимает, клиент привязывается к `S3ClientConfigWithCredentials`,
и секция `credentials { accessKey, secretKey }` становится `обязательной`.

### Получение файла { #get-file }

В разделе описана операция получения объекта с помощью декларативного S3-клиента.
Для указания операции предлагается использовать аннотацию `@S3.Get`.

Тип возвращаемого значения — либо [`GetObjectResult`](#model-get-object-result), то есть «сырой» ответ,
тело которого читается потоком, либо `byte[]` / `ByteArray`, и тогда клиент вычитывает всё тело в память
и закрывает ответ за вас.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient")
    @S3.Bucket(".bucket")
    public interface SomeClient {

        @S3.Get //(1)!
        GetObjectResult operation1(String key); //(2)!

        @S3.Get
        byte[] operation2(String key); //(3)!

        @S3.Get("some-key") //(4)!
        GetObjectResult operation3();
    }
    ```

    1. Операция получения объекта
    2. Полный ответ с потоковым телом; закрывать его должен вызывающий код
    3. Объект целиком вычитывается в память, ответ закрывает сам клиент
    4. Ключ объекта можно указать в аннотации

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    @S3.Bucket(".bucket")
    interface SomeClient {

        @S3.Get //(1)!
        fun operation1(key: String): GetObjectResult //(2)!

        @S3.Get
        fun operation2(key: String): ByteArray //(3)!

        @S3.Get("some-key") //(4)!
        fun operation3(): GetObjectResult
    }
    ```

    1. Операция получения объекта
    2. Полный ответ с потоковым телом; закрывать его должен вызывающий код
    3. Объект целиком вычитывается в память, ответ закрывает сам клиент
    4. Ключ объекта можно указать в аннотации

`GetObjectResult` является `HttpClientResponse` и потому `Closeable`. Чтение тела означает закрытие
и самого ответа, и тела:

===! ":fontawesome-brands-java: `Java`"

    ```java
    try (var response = client.operation1("report.pdf");
         var body = response.body();
         var stream = body.asInputStream()) {
        return stream.readAllBytes();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    client.operation1("report.pdf").use { response ->
        response.body().asInputStream().use { stream ->
            return stream.readAllBytes()
        }
    }
    ```

Любой другой тип возвращаемого значения — ошибка компиляции:
`S3 operation '@S3.Get' on method '...' has unsupported return type`.

#### Шаблон ключа { #key-template }

Ключ можно задать в виде шаблона и подставлять в него аргументы метода;
все ключевые аргументы метода должны быть частью шаблона.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient")
    @S3.Bucket(".bucket")
    public interface SomeClient {

        @S3.Get("prefix-{key1}-{key2}-suffix") //(1)!
        GetObjectResult operation(String key1, int key2); //(2)!
    }
    ```

    1. Шаблон, используемый для построения ключа: каждый аргумент шаблона подставляется через `String.valueOf()`, а аргументы шаблона указываются как имена аргументов метода в `{фигурных скобках}`
    2. Все ключевые аргументы метода должны быть частью шаблона ключа

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    @S3.Bucket(".bucket")
    interface SomeClient {

        @S3.Get("prefix-{key1}-{key2}-suffix") //(1)!
        fun operation(key1: String, key2: Int): GetObjectResult //(2)!
    }
    ```

    1. Шаблон, используемый для построения ключа: каждый аргумент шаблона подставляется через `String.valueOf()`, а аргументы шаблона указываются как имена аргументов метода в `{фигурных скобках}`
    2. Все ключевые аргументы метода должны быть частью шаблона ключа

Параметры, которые **не** являются частями ключа и потому никогда не попадают в шаблон:

- параметр с аннотацией [`@S3.Bucket`](#bucket)
- параметр типа [`S3Credentials`](#credentials)
- параметр [типа аргументов](#model-request-args) — `GetObjectArgs`, `HeadObjectArgs`, `ListObjectsArgs`, `PutObjectArgs`, `DeleteObjectArgs`
- параметр [тела](#file-body) — `byte[]`, `ByteBuffer`, `InputStream`, `S3Client.ContentWriter`

Без шаблона метод должен иметь ровно один ключевой параметр, и ключом становится его `String.valueOf()`.
Неоднозначные случаи процессор отклоняет с явными сообщениями:

| Ситуация                                          | Ошибка компиляции                                                             |
|---------------------------------------------------|-------------------------------------------------------------------------------|
| Несколько ключевых параметров и нет шаблона       | `has N key parameters, but no key template`                                   |
| Нет ключевого параметра и нет константного ключа  | `has no object key`                                                           |
| Шаблон ссылается на неизвестный параметр          | `references key template parameter '{x}', but the method has no matching key parameter` |
| Шаблон без закрывающей фигурной скобки            | `has malformed key template ...: missing closing '}'`                         |
| Коллекция или map в качестве параметра шаблона    | `uses '{x}' in the key template, but parameter 'x' is a collection or map`     |
| Коллекция в качестве единственного ключа          | `expects one object key, but parameter 'x' is a collection`                   |

#### Необязательный ответ { #optional-get }

Если отсутствие объекта — нормальный исход, а не ошибка, пометьте метод как nullable.
В `Java` используется аннотация `@Nullable` из [JSpecify](https://jspecify.dev), в `Kotlin` — nullable-тип
возвращаемого значения. Такая операция возвращает `null` вместо выбрасывания [`S3ClientNoSuchKeyException`](#not-found-exception).

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient")
    @S3.Bucket(".bucket")
    public interface SomeClient {

        @S3.Get
        @Nullable //(1)!
        GetObjectResult object(String key);

        @S3.Head
        @Nullable
        HeadObjectResult meta(String key);
    }
    ```

    1. `org.jspecify.annotations.Nullable`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    @S3.Bucket(".bucket")
    interface SomeClient {

        @S3.Get
        fun `object`(key: String): GetObjectResult? //(1)!

        @S3.Head
        fun meta(key: String): HeadObjectResult?
    }
    ```

    1. Nullable-тип возвращаемого значения делает операцию необязательной

То же самое работает для результатов `byte[]` / `ByteArray` операции `@S3.Get`.

#### Аргументы запроса { #get-args }

Операция может принимать [объект аргументов](#model-request-args), который несёт всё, что поддерживает
API `S3` помимо бакета и ключа — условные заголовки, идентификатор версии, переопределение заголовков ответа,
параметры серверного шифрования и [диапазон байт](#range):

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient")
    @S3.Bucket(".bucket")
    public interface SomeClient {

        @S3.Get("prefix-{key}")
        GetObjectResult operation(String key, GetObjectArgs args); //(1)!
    }
    ```

    1. Параметр `GetObjectArgs` передаётся в запрос `S3` как есть и не входит в ключ

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    @S3.Bucket(".bucket")
    interface SomeClient {

        @S3.Get("prefix-{key}")
        fun operation(key: String, args: GetObjectArgs): GetObjectResult //(1)!
    }
    ```

    1. Параметр `GetObjectArgs` передаётся в запрос `S3` как есть и не входит в ключ

Объекты аргументов — изменяемые контейнеры с публичными полями:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var args = new GetObjectArgs();
    args.versionId = "3HL4kqtJlcpXroDTDmJ+rmSpXd3dIbrHY+MTRCxf3vjVBH40Nr8X8gdRQBpUMLUo";
    args.ifNoneMatch = etag;

    var result = client.operation("report.pdf", args);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val args = GetObjectArgs()
    args.versionId = "3HL4kqtJlcpXroDTDmJ+rmSpXd3dIbrHY+MTRCxf3vjVBH40Nr8X8gdRQBpUMLUo"
    args.ifNoneMatch = etag

    val result = client.operation("report.pdf", args)
    ```

#### Диапазон байт { #range }

`GetObjectArgs` и `HeadObjectArgs` принимают `Range`, который отображается в
[HTTP-заголовок `Range`](https://www.rfc-editor.org/rfc/rfc9110.html#name-range). `Range` — это sealed-интерфейс
с тремя фабриками:

| Фабрика                            | Смысл                                                            | Значение заголовка  |
|------------------------------------|------------------------------------------------------------------|---------------------|
| `Range.fromTo(first, last)`        | Байты с `first` по `last` включительно                            | `bytes=first-last`  |
| `Range.from(first)`                | Байты с `first` до конца объекта                                  | `bytes=first-`      |
| `Range.last(bytes)`                | Последние `bytes` байт объекта                                    | `bytes=-bytes`      |

===! ":fontawesome-brands-java: `Java`"

    ```java
    var args = new GetObjectArgs();
    args.range = Range.fromTo(0, 1023); //(1)!

    try (var response = client.operation("video.mp4", args)) {
        var range = response.contentRange(); //(2)!
    }
    ```

    1. Первый килобайт объекта
    2. `ContentRange(firstPosition, lastPosition, completeLength)`, разобранный из заголовка `Content-Range`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val args = GetObjectArgs()
    args.range = Range.fromTo(0, 1023) //(1)!

    client.operation("video.mp4", args).use { response ->
        val range = response.contentRange() //(2)!
    }
    ```

    1. Первый килобайт объекта
    2. `ContentRange(firstPosition, lastPosition, completeLength)`, разобранный из заголовка `Content-Range`

### Метаданные { #metadata }

Операция `@S3.Head` получает метаданные объекта, не передавая его тело, поэтому она значительно дешевле
[получения объекта](#get-file). Единственный поддерживаемый тип ответа —
[`HeadObjectResult`](#model-head-object-result).

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient")
    @S3.Bucket(".bucket")
    public interface SomeClient {

        @S3.Head //(1)!
        HeadObjectResult operation1(String key);

        @S3.Head("some-key") //(2)!
        HeadObjectResult operation2();

        @S3.Head
        HeadObjectResult operation3(String key, HeadObjectArgs args); //(3)!
    }
    ```

    1. Операция получения метаданных
    2. Ключ объекта можно указать в аннотации
    3. Поддерживает ту же механику [объекта аргументов](#model-request-args), что и `@S3.Get`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    @S3.Bucket(".bucket")
    interface SomeClient {

        @S3.Head //(1)!
        fun operation1(key: String): HeadObjectResult

        @S3.Head("some-key") //(2)!
        fun operation2(): HeadObjectResult

        @S3.Head
        fun operation3(key: String, args: HeadObjectArgs): HeadObjectResult //(3)!
    }
    ```

    1. Операция получения метаданных
    2. Ключ объекта можно указать в аннотации
    3. Поддерживает ту же механику [объекта аргументов](#model-request-args), что и `@S3.Get`

!!! note "У HEAD нет тела ответа"

    На `HEAD`-запрос отсутствующего объекта `S3` отвечает кодом `404` и пустым телом, поэтому код ошибки
    хранилища прочитать невозможно. И отсутствующий объект, и отсутствующий бакет проявляются как сбой вида
    [`S3ClientNoSuchKeyException`](#not-found-exception) с `errorCode` равным `NoSuchKey` —
    не используйте `@S3.Head`, чтобы отличить одно от другого.

### Получение списка файлов { #list-files }

В разделе описана операция получения списка объектов с помощью декларативного S3-клиента.
Для указания операции предлагается использовать аннотацию `@S3.List`.

[Префикс ключа](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-prefixes.html) может быть
константой в аннотации, шаблоном, построенным из аргументов метода, либо полем параметра
[`ListObjectsArgs`](#list-args).

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient")
    @S3.Bucket(".bucket")
    public interface SomeClient {

        @S3.List
        ListBucketResult operation1(String prefix); //(1)!

        @S3.List("some-prefix-") //(2)!
        ListBucketResult operation2();

        @S3.List("prefix-{key}-") //(3)!
        ListBucketResult operation3(String key);
    }
    ```

    1. Префикс передан как аргумент метода, поскольку он не указан в аннотации
    2. Константный префикс, указанный в аннотации
    3. Префикс, построенный по [шаблону](#prefix-template)

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    @S3.Bucket(".bucket")
    interface SomeClient {

        @S3.List
        fun operation1(prefix: String): ListBucketResult //(1)!

        @S3.List("some-prefix-") //(2)!
        fun operation2(): ListBucketResult

        @S3.List("prefix-{key}-") //(3)!
        fun operation3(key: String): ListBucketResult
    }
    ```

    1. Префикс передан как аргумент метода, поскольку он не указан в аннотации
    2. Константный префикс, указанный в аннотации
    3. Префикс, построенный по [шаблону](#prefix-template)

Поддерживаемые типы возвращаемых значений:

| Тип возвращаемого значения                      | Описание                                                                               |
|-------------------------------------------------|----------------------------------------------------------------------------------------|
| `ListBucketResult`                              | Одна страница списка вместе с `keyCount`, `commonPrefixes` и токеном продолжения        |
| `List<ListBucketResult.ListBucketItem>`         | Элементы одной страницы                                                                 |
| `List<String>`                                  | Ключи одной страницы                                                                    |
| `Iterator<ListBucketResult.ListBucketItem>`     | [Ленивый итератор](#list-iterator) по всем страницам                                    |
| `Iterator<String>`                              | [Ленивый итератор](#list-iterator) по ключам всех страниц                               |

Любой другой тип возвращаемого значения — ошибка компиляции с перечислением ровно этих пяти вариантов.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient")
    @S3.Bucket(".bucket")
    public interface SomeClient {

        @S3.List
        List<String> keys(String prefix); //(1)!

        @S3.List
        List<ListBucketResult.ListBucketItem> items(String prefix); //(2)!
    }
    ```

    1. Только ключи объектов первой страницы
    2. Полные элементы первой страницы с размером, `ETag` и временем изменения

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    @S3.Bucket(".bucket")
    interface SomeClient {

        @S3.List
        fun keys(prefix: String): List<String> //(1)!

        @S3.List
        fun items(prefix: String): List<ListBucketResult.ListBucketItem> //(2)!
    }
    ```

    1. Только ключи объектов первой страницы
    2. Полные элементы первой страницы с размером, `ETag` и временем изменения

!!! warning "Операции получения списка нужен источник префикса"

    Без значения аннотации, без ключевого параметра и без параметра `ListObjectsArgs` процессор падает
    с ошибкой `S3 operation '...' has no object key`. Если цель — перечислить весь бакет, передайте
    `ListObjectsArgs` с явно пустым префиксом.

#### Шаблон префикса { #prefix-template }

Префикс также можно задать в виде шаблона и подставлять в него аргументы метода как часть шаблона;
все ключевые аргументы метода должны быть частью шаблона.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient")
    @S3.Bucket(".bucket")
    public interface SomeClient {

        @S3.List("prefix-{key1}-{key2}-") //(1)!
        ListBucketResult operation(String key1, int key2);
    }
    ```

    1. Шаблон, используемый для построения префикса: каждый аргумент шаблона подставляется через `String.valueOf()`, а аргументы шаблона указываются как имена аргументов метода в `{фигурных скобках}`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    @S3.Bucket(".bucket")
    interface SomeClient {

        @S3.List("prefix-{key1}-{key2}-") //(1)!
        fun operation(key1: String, key2: Int): ListBucketResult
    }
    ```

    1. Шаблон, используемый для построения префикса: каждый аргумент шаблона подставляется через `String.valueOf()`, а аргументы шаблона указываются как имена аргументов метода в `{фигурных скобках}`

#### Аргументы списка { #list-args }

Параметр `ListObjectsArgs` полностью заменяет префикс, задаваемый аннотацией: объект передаётся
в хранилище как есть, поэтому префикс, размер страницы и токен продолжения берутся из него.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient")
    @S3.Bucket(".bucket")
    public interface SomeClient {

        @S3.List
        ListBucketResult operation(ListObjectsArgs args); //(1)!
    }
    ```

    1. Когда присутствует параметр `ListObjectsArgs`, значение аннотации и ключевые параметры для построения префикса не используются

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    @S3.Bucket(".bucket")
    interface SomeClient {

        @S3.List
        fun operation(args: ListObjectsArgs): ListBucketResult //(1)!
    }
    ```

    1. Когда присутствует параметр `ListObjectsArgs`, значение аннотации и ключевые параметры для построения префикса не используются

Ручная постраничная выборка через `ListBucketResult`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var args = new ListObjectsArgs();
    args.prefix = "2024/";
    args.maxKeys = 100; //(1)!

    ListBucketResult page;
    do {
        page = client.operation(args);
        for (var item : page.items()) {
            // ...
        }
        args.continuationToken = page.nextContinuationToken(); //(2)!
    } while (args.continuationToken != null);
    ```

    1. Размер страницы; независимо от значения хранилище возвращает не более `1000` ключей за запрос
    2. `null`, когда прочитана последняя страница

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val args = ListObjectsArgs()
    args.prefix = "2024/"
    args.maxKeys = 100 //(1)!

    do {
        val page = client.operation(args)
        for (item in page.items()) {
            // ...
        }
        args.continuationToken = page.nextContinuationToken() //(2)!
    } while (args.continuationToken != null)
    ```

    1. Размер страницы; независимо от значения хранилище возвращает не более `1000` ключей за запрос
    2. `null`, когда прочитана последняя страница

#### Разделитель { #separator }

[Разделитель](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-prefixes.html) группирует ключи
с общим префиксом до указанного символа — именно так в `S3` эмулируются «каталоги».
Он задаётся через `ListObjectsArgs.delimiter`, а сгруппированные префиксы возвращаются в
`ListBucketResult.commonPrefixes()`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var args = new ListObjectsArgs();
    args.prefix = "documents/";
    args.delimiter = "/"; //(1)!

    var result = client.operation(args);
    var directories = result.commonPrefixes(); //(2)!
    var files = result.items(); //(3)!
    ```

    1. Сгруппировать всё, что находится ниже `documents/`, по следующему `/`
    2. Псевдокаталоги вида `documents/2024/`
    3. Объекты, лежащие непосредственно в `documents/`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val args = ListObjectsArgs()
    args.prefix = "documents/"
    args.delimiter = "/" //(1)!

    val result = client.operation(args)
    val directories = result.commonPrefixes() //(2)!
    val files = result.items() //(3)!
    ```

    1. Сгруппировать всё, что находится ниже `documents/`, по следующему `/`
    2. Псевдокаталоги вида `documents/2024/`
    3. Объекты, лежащие непосредственно в `documents/`

#### Итераторы { #list-iterator }

Возврат `Iterator` полностью скрывает постраничную выборку: клиент запрашивает следующую страницу только
после того, как текущая исчерпана. Это рекомендуемый способ обойти большой бакет, не держа весь список
в памяти.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient")
    @S3.Bucket(".bucket")
    public interface SomeClient {

        @S3.List
        Iterator<String> allKeys(String prefix); //(1)!

        @S3.List
        Iterator<ListBucketResult.ListBucketItem> allItems(ListObjectsArgs args); //(2)!
    }
    ```

    1. Лениво перебирает ключи всех страниц
    2. Лениво перебирает элементы всех страниц

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    @S3.Bucket(".bucket")
    interface SomeClient {

        @S3.List
        fun allKeys(prefix: String): Iterator<String> //(1)!

        @S3.List
        fun allItems(args: ListObjectsArgs): Iterator<ListBucketResult.ListBucketItem> //(2)!
    }
    ```

    1. Лениво перебирает ключи всех страниц
    2. Лениво перебирает элементы всех страниц

### Добавление файла { #add-file }

В разделе описана операция добавления объекта с помощью декларативного S3-клиента.
Для операции предлагается использовать аннотацию `@S3.Put`.

Метод должен объявлять ровно один параметр тела и возвращать либо `String` — `ETag`, сообщённый
хранилищем, — либо `void` / `Unit`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient")
    @S3.Bucket(".bucket")
    public interface SomeClient {

        @S3.Put
        String operation1(String key, //(1)!
                          byte[] body); //(2)!

        @S3.Put("some-key") //(3)!
        void operation2(byte[] body); //(4)!
    }
    ```

    1. Ключ объекта, по которому он будет добавлен в хранилище
    2. Тело объекта, которое будет загружено
    3. Ключ также можно указать в аннотации, если он статический
    4. `void`, когда `ETag` не нужен

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    @S3.Bucket(".bucket")
    interface SomeClient {

        @S3.Put
        fun operation1(key: String, //(1)!
                       body: ByteArray): String //(2)!

        @S3.Put("some-key") //(3)!
        fun operation2(body: ByteArray) //(4)!
    }
    ```

    1. Ключ объекта, по которому он будет добавлен в хранилище
    2. Тело объекта, которое будет загружено
    3. Ключ также можно указать в аннотации, если он статический
    4. `Unit`, когда `ETag` не нужен

Любой другой тип возвращаемого значения падает на этапе компиляции с ошибкой
`S3 operation '@S3.Put' on method '...' has unsupported return type`, ожидающей `String or void`.

#### Тело файла { #file-body }

Требуется ровно один параметр тела, и его тип определяет способ загрузки:

| Тип тела                   | Тип в Kotlin              | Стратегия загрузки                                                                                       |
|----------------------------|---------------------------|-----------------------------------------------------------------------------------------------------------|
| `byte[]`                   | `ByteArray`               | Одиночный `PUT` всего массива                                                                             |
| `ByteBuffer`               | `ByteBuffer`              | Одиночный `PUT` `remaining()` байт; heap-буфер используется напрямую, direct-буфер сначала копируется     |
| `InputStream`              | `InputStream`             | [Многочастная загрузка](#multipart-upload), управляемая параметром `upload.partSize`                       |
| `S3Client.ContentWriter`   | `S3Client.ContentWriter`  | Потоковый `PUT` с кодированием `aws-chunked`, размер чанка из `upload.chunkSize`                           |

`ContentWriter` — способ передать потоком тело известной длины, не материализуя его:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient")
    @S3.Bucket(".bucket")
    public interface SomeClient {

        @S3.Put("some-key")
        String operation(S3Client.ContentWriter body);
    }
    ```

    ```java
    var file = Path.of("/tmp/report.pdf");
    var etag = client.operation(new S3Client.ContentWriter() {

        @Override
        public void write(OutputStream os) throws IOException { //(1)!
            Files.copy(file, os);
        }

        @Override
        public long length() { //(2)!
            return Files.size(file);
        }
    });
    ```

    1. Вызывается клиентом во время записи тела запроса
    2. Точная длина содержимого, необходимая для подписания запроса

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    @S3.Bucket(".bucket")
    interface SomeClient {

        @S3.Put("some-key")
        fun operation(body: S3Client.ContentWriter): String
    }
    ```

    ```kotlin
    val file = Path.of("/tmp/report.pdf")
    val etag = client.operation(object : S3Client.ContentWriter {

        override fun write(os: OutputStream) { //(1)!
            Files.copy(file, os)
        }

        override fun length(): Long = Files.size(file) //(2)!
    })
    ```

    1. Вызывается клиентом во время записи тела запроса
    2. Точная длина содержимого, необходимая для подписания запроса

!!! warning "Тип тела"

    Метод `@S3.Put` без параметра тела падает с ошибкой `has no upload body parameter`, а метод более чем
    с одним параметром тела — с ошибкой `has N upload body parameters, but only one body parameter is supported`.
    Неподдерживаемый тип тела падает с ошибкой `has unsupported body type`.

#### Шаблон ключа { #key-template-2 }

Ключ также можно задать в виде шаблона и подставлять в него аргументы метода как часть шаблона;
все ключевые аргументы метода должны быть частью шаблона.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient")
    @S3.Bucket(".bucket")
    public interface SomeClient {

        @S3.Put("prefix-{key1}-{key2}-suffix") //(1)!
        String operation(String key1, int key2, byte[] body); //(2)!
    }
    ```

    1. Шаблон, используемый для построения ключа: каждый аргумент шаблона подставляется через `String.valueOf()`, а аргументы шаблона указываются как имена аргументов метода в `{фигурных скобках}`
    2. Параметр тела никогда не входит в шаблон ключа

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    @S3.Bucket(".bucket")
    interface SomeClient {

        @S3.Put("prefix-{key1}-{key2}-suffix") //(1)!
        fun operation(key1: String, key2: Int, body: ByteArray): String //(2)!
    }
    ```

    1. Шаблон, используемый для построения ключа: каждый аргумент шаблона подставляется через `String.valueOf()`, а аргументы шаблона указываются как имена аргументов метода в `{фигурных скобках}`
    2. Параметр тела никогда не входит в шаблон ключа

#### Тип и кодировка содержимого { #content-type }

`Content-Type`, `Content-Encoding` и все остальные заголовки загрузки задаются через параметр
`PutObjectArgs`, а не через аннотацию:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient")
    @S3.Bucket(".bucket")
    public interface SomeClient {

        @S3.Put("prefix-{key}")
        String operation(String key, PutObjectArgs args, byte[] body);
    }
    ```

    ```java
    var args = new PutObjectArgs();
    args.contentType = "image/jpeg"; //(1)!
    args.contentEncoding = "gzip"; //(2)!
    args.storageClass = "STANDARD_IA"; //(3)!
    args.tagging = "project=reports&owner=team"; //(4)!

    var etag = client.operation("avatar", args, bytes);
    ```

    1. `Content-Type` объекта
    2. `Content-Encoding` объекта
    3. Класс хранения объекта
    4. Теги объекта в формате `URL`-запроса

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    @S3.Bucket(".bucket")
    interface SomeClient {

        @S3.Put("prefix-{key}")
        fun operation(key: String, args: PutObjectArgs, body: ByteArray): String
    }
    ```

    ```kotlin
    val args = PutObjectArgs()
    args.contentType = "image/jpeg" //(1)!
    args.contentEncoding = "gzip" //(2)!
    args.storageClass = "STANDARD_IA" //(3)!
    args.tagging = "project=reports&owner=team" //(4)!

    val etag = client.operation("avatar", args, bytes)
    ```

    1. `Content-Type` объекта
    2. `Content-Encoding` объекта
    3. Класс хранения объекта
    4. Теги объекта в формате `URL`-запроса

#### Многочастная загрузка { #multipart-upload }

Тело типа `InputStream` загружается многочастной загрузкой без дополнительного кода. Клиент читает поток
кусками по `upload.partSize`; если весь поток укладывается в первый кусок, он отправляется одним `PUT`,
и многочастная загрузка вообще не начинается.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient")
    @S3.Bucket(".bucket")
    public interface SomeClient {

        @S3.Put("prefix-{key}")
        String operation(String key, InputStream body); //(1)!
    }
    ```

    1. Поток закрывается клиентом по завершении загрузки

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    @S3.Bucket(".bucket")
    interface SomeClient {

        @S3.Put("prefix-{key}")
        fun operation(key: String, body: InputStream): String //(1)!
    }
    ```

    1. Поток закрывается клиентом по завершении загрузки

===! ":material-code-json: `Hocon`"

    ```javascript
    s3client.someClient {
        upload {
            partSize = "16MiB" //(1)!
        }
    }
    ```

    1.  Размер части для загрузки из `InputStream`, по спецификации `S3` должен быть от `5MiB` до `5GiB` (по умолчанию: `5MiB`)

=== ":simple-yaml: `YAML`"

    ```yaml
    s3client:
      someClient:
        upload:
          partSize: "16MiB" #(1)!
    ```

    1.  Размер части для загрузки из `InputStream`, по спецификации `S3` должен быть от `5MiB` до `5GiB` (по умолчанию: `5MiB`)

Параметр `PutObjectArgs` учитывается и здесь: его значения транслируются в аргументы
`CreateMultipartUpload` и `CompleteMultipartUpload`.

Если при чтении потока происходит `IOException`, клиент перевыбрасывает его как
[`S3ClientUnknownException`](#unknown-exception).

### Удаление файла { #delete-file }

В разделе описана операция удаления объекта с помощью декларативного S3-клиента.
Для операции предлагается использовать аннотацию `@S3.Delete`. Тип возвращаемого значения должен быть
`void` / `Unit`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient")
    @S3.Bucket(".bucket")
    public interface SomeClient {

        @S3.Delete //(1)!
        void operation1(String key); //(2)!

        @S3.Delete("some-key") //(3)!
        void operation2();

        @S3.Delete
        void operation3(String key, DeleteObjectArgs args); //(4)!
    }
    ```

    1. Операция удаления объекта
    2. Ключ удаляемого объекта
    3. Ключ объекта можно указать в аннотации
    4. Идентификатор версии, `MFA` и параметры условного удаления

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    @S3.Bucket(".bucket")
    interface SomeClient {

        @S3.Delete //(1)!
        fun operation1(key: String) //(2)!

        @S3.Delete("some-key") //(3)!
        fun operation2()

        @S3.Delete
        fun operation3(key: String, args: DeleteObjectArgs) //(4)!
    }
    ```

    1. Операция удаления объекта
    2. Ключ удаляемого объекта
    3. Ключ объекта можно указать в аннотации
    4. Идентификатор версии, `MFA` и параметры условного удаления

Удаление несуществующего объекта — как и объекта в несуществующем бакете — не является ошибкой:
`S3` отвечает на такой `DELETE` успехом.

!!! warning "В декларативном клиенте нет пакетного удаления"

    `@S3.Delete` всегда генерирует запрос `DeleteObject` для одного объекта. Метод вида
    `void operation(List<String> keys)` **не** поддерживается и падает на этапе компиляции, поскольку
    коллекция не может быть ключом объекта. Пакетное удаление доступно через
    [императивный клиент](#client-imperative) — `S3Client#deleteObjects` — либо через
    [клиент AWS SDK](#aws).

#### Шаблон ключа { #key-template-3 }

Ключ также можно задать в виде шаблона и подставлять в него аргументы метода как часть шаблона;
все ключевые аргументы метода должны быть частью шаблона.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient")
    @S3.Bucket(".bucket")
    public interface SomeClient {

        @S3.Delete("prefix-{key1}-{key2}-suffix") //(1)!
        void operation(String key1, int key2); //(2)!
    }
    ```

    1. Шаблон, используемый для построения ключа: каждый аргумент шаблона подставляется через `String.valueOf()`, а аргументы шаблона указываются как имена аргументов метода в `{фигурных скобках}`
    2. Все ключевые аргументы метода должны быть частью шаблона ключа

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    @S3.Bucket(".bucket")
    interface SomeClient {

        @S3.Delete("prefix-{key1}-{key2}-suffix") //(1)!
        fun operation(key1: String, key2: Int) //(2)!
    }
    ```

    1. Шаблон, используемый для построения ключа: каждый аргумент шаблона подставляется через `String.valueOf()`, а аргументы шаблона указываются как имена аргументов метода в `{фигурных скобках}`
    2. Все ключевые аргументы метода должны быть частью шаблона ключа

### Пользовательская фабрика { #factory-tag }

Каждый сгенерированный клиент запрашивает из графа `S3ClientFactory` и создаёт через неё свой `S3Client`.
Атрибут `factoryTag` аннотации `@S3.Client` заставляет клиент запрашивать **помеченную тегом** фабрику
вместо фабрики по умолчанию — так одно приложение может держать клиенты на разных транспортах или
с разной настройкой телеметрии:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client(value = "s3client.someClient", factoryTag = SomeClient.CustomFactory.class) //(1)!
    @S3.Bucket(".bucket")
    public interface SomeClient {

        final class CustomFactory {} //(2)!

        @S3.Get
        GetObjectResult operation(String key);
    }
    ```

    1. Сгенерированному модулю требуется `@Tag(SomeClient.CustomFactory.class) S3ClientFactory`
    2. В качестве маркера тега подходит любой класс

    ```java
    @KoraApp
    public interface Application extends KoraS3ClientModule {

        @Tag(SomeClient.CustomFactory.class)
        default S3ClientFactory customS3ClientFactory(@Tag(CustomS3.class) HttpClient httpClient, //(1)!
                                                      S3ClientTelemetryFactory telemetryFactory) {
            return (configPath, clientImpl, config) -> {
                var telemetry = telemetryFactory.get(configPath, clientImpl, config.telemetry());
                return new KoraS3Client(httpClient, config, telemetry);
            };
        }
    }
    ```

    1. Отдельный `HTTP`-клиент только для этого `S3`-клиента

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client(value = "s3client.someClient", factoryTag = SomeClient.CustomFactory::class) //(1)!
    @S3.Bucket(".bucket")
    interface SomeClient {

        class CustomFactory //(2)!

        @S3.Get
        fun operation(key: String): GetObjectResult
    }
    ```

    1. Сгенерированному модулю требуется `@Tag(SomeClient.CustomFactory::class) S3ClientFactory`
    2. В качестве маркера тега подходит любой класс

    ```kotlin
    @KoraApp
    interface Application : KoraS3ClientModule {

        @Tag(SomeClient.CustomFactory::class)
        fun customS3ClientFactory(@Tag(CustomS3::class) httpClient: HttpClient, //(1)!
                                  telemetryFactory: S3ClientTelemetryFactory): S3ClientFactory =
            S3ClientFactory { configPath, clientImpl, config ->
                val telemetry = telemetryFactory.get(configPath, clientImpl, config.telemetry())
                KoraS3Client(httpClient, config, telemetry)
            }
    }
    ```

    1. Отдельный `HTTP`-клиент только для этого `S3`-клиента

Без `factoryTag` используется фабрика `S3ClientFactory` по умолчанию из `KoraS3ClientModule`: она берёт
`HttpClient` из графа и подключает телеметрию модуля.

### Сигнатуры { #signatures }

Доступные из коробки сигнатуры методов декларативного `S3`-клиента:

===! ":fontawesome-brands-java: `Java`"

    Под `T` подразумевается тип возвращаемого значения.

    - `T myMethod()`

=== ":simple-kotlin: `Kotlin`"

    Под `T` подразумевается тип возвращаемого значения, либо `T?`, либо `Unit`.

    - `fun myMethod(): T`

`S3`-клиенты **синхронные**. Сигнатур с `CompletionStage`, `CompletableFuture`, `Mono` или `Flux` нет,
а `suspend`-функция отклоняется процессором символов с явной ошибкой
`Suspend methods are not supported by the S3 client generator`. Выполняйте блокирующие операции
параллельно средствами платформы, например на виртуальных потоках.

## Модели { #models }

Все типы моделей находятся в пакете `io.koraframework.s3.client.kora.model` и его подпакетах `request` / `response`.

### GetObjectResult { #model-get-object-result }

Результат операции [получения объекта](#get-file). Расширяет `HttpClientResponse`, поэтому предоставляет
«сырой» `HTTP`-ответ и требует закрытия:

| Метод                           | Описание                                                                          |
|---------------------------------|-----------------------------------------------------------------------------------|
| `int code()`                    | Код статуса `HTTP` ответа                                                          |
| `HttpHeaders headers()`         | Заголовки `HTTP`-ответа                                                            |
| `HttpBodyInput body()`          | Тело объекта, читается через `asInputStream()`                                     |
| `ContentRange contentRange()`   | Разобранный заголовок `Content-Range`, осмысленный только для [ranged](#range)-запроса |
| `void close()`                  | Освобождает ответ и нижележащее соединение                                         |

`ContentRange` — это record с полями `firstPosition`, `lastPosition` и `completeLength`.
Метод `contentRange()` выбрасывает `IllegalArgumentException`, если в ответе нет заголовка `Content-Range`.

### HeadObjectResult { #model-head-object-result }

Результат операции [получения метаданных](#metadata), record с лениво разбираемыми заголовками:

| Метод                        | Описание                                                                 |
|------------------------------|--------------------------------------------------------------------------|
| `String bucket()`            | Бакет, которому принадлежит объект                                        |
| `String key()`               | Ключ объекта                                                              |
| `long size()`                | Размер объекта в байтах                                                   |
| `HttpHeaders headers()`      | Все заголовки ответа                                                      |
| `String etag()`              | Значение заголовка `ETag`                                                 |
| `String versionId()`         | Значение заголовка `x-amz-version-id`                                     |
| `Instant lastModified()`     | Разобранный заголовок `Last-Modified` либо `null`, если заголовка нет      |

### ListBucketResult { #model-list-bucket-result }

Результат операции [получения списка](#list-files):

| Метод                               | Описание                                                                                     |
|-------------------------------------|-----------------------------------------------------------------------------------------------|
| `List<ListBucketItem> items()`      | Объекты текущей страницы                                                                      |
| `int keyCount()`                    | Количество ключей, возвращённых на этой странице                                               |
| `List<String> commonPrefixes()`     | Сгруппированные префиксы, если использовался [разделитель](#separator), иначе `null`            |
| `String nextContinuationToken()`    | Токен следующей страницы либо `null` на последней странице                                     |

`ListBucketResult.ListBucketItem` — это record, описывающий один объект:

| Компонент                    | Описание                                                          |
|------------------------------|-------------------------------------------------------------------|
| `String bucket()`            | Бакет, которому принадлежит объект                                 |
| `String key()`               | Ключ объекта                                                       |
| `String etag()`              | `ETag` объекта                                                     |
| `String checksumType()`      | Тип контрольной суммы, сообщённый хранилищем                       |
| `String checksumAlgorithm()` | Алгоритм контрольной суммы, сообщённый хранилищем                  |
| `Instant lastModified()`     | Время последнего изменения                                         |
| `long size()`                | Размер объекта в байтах                                            |
| `String storageClass()`      | Класс хранения, `null` если не сообщён                             |
| `ListBucketItemOwner owner()`| Владелец (`displayName`, `id`), `null` если не задан `fetchOwner`  |

### Аргументы запроса { #model-request-args }

Объекты аргументов — обычные изменяемые классы с публичными полями, по одному на параметр запроса `S3`.
Их можно передавать в любую подходящую декларативную операцию или в [императивный клиент](#client-imperative).

| Тип                 | Значимые поля                                                                                                                                                                                                           |
|---------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `GetObjectArgs`     | `range`, `versionId`, `partNumber`, `ifMatch`, `ifNoneMatch`, `ifModifiedSince`, `ifUnmodifiedSince`, `responseContentType`, `responseContentDisposition`, `responseContentEncoding`, `responseContentLanguage`, `responseCacheControl`, `responseExpires`, `sseCustomerAlgorithm`, `sseCustomerKey`, `checksumMode`, `requestPayer`, `expectedBucketOwner` |
| `HeadObjectArgs`    | Тот же набор полей, что и у `GetObjectArgs`                                                                                                                                                                               |
| `ListObjectsArgs`   | `prefix`, `delimiter`, `maxKeys`, `continuationToken`, `startAfter`, `fetchOwner`, `optionalObjectAttributes`, `requestPayer`, `expectedBucketOwner`                                                                       |
| `PutObjectArgs`     | `contentType`, `contentEncoding`, `contentDisposition`, `contentLanguage`, `cacheControl`, `expires`, `acl`, `storageClass`, `tagging`, `ifMatch`, `ifNoneMatch`, `serverSideEncryption`, `sseCustomerAlgorithm`, `sseCustomerKey`, `sseKmsKeyId`, `sseKmsEncryptionContext`, `bucketKeyEnabled`, `objectLockMode`, `objectLockRetainUntilDate`, `objectLockLegalHoldStatus`, `grantRead`, `grantReadAcp`, `grantWriteAcp`, `grantFullControl`, `websiteRedirectLocation`, `requestPayer`, `expectedBucketOwner` |
| `DeleteObjectArgs`  | `versionId`, `mfa`, `bypassGovernanceRetention`, `ifMatch`, `ifMatchLastModifiedTime`, `ifMatchSize`, `requestPayer`, `expectedBucketOwner`                                                                                |

Типы для многочастной загрузки — `CreateMultipartUploadArgs`, `UploadPartArgs`, `CompleteMultipartUploadArgs`,
`AbortMultipartUploadArgs`, `ListPartsArgs` и `ListMultipartUploadsArgs` — устроены так же и используются
[императивным клиентом](#client-imperative).
Методы `CreateMultipartUploadArgs.from(PutObjectArgs)` и `CompleteMultipartUploadArgs.from(PutObjectArgs)`
преобразуют аргументы загрузки для многочастного сценария — именно это делает сгенерированный клиент
для тела типа `InputStream`.

## Императивный клиент { #client-imperative }

`io.koraframework.s3.client.kora.S3Client` — это низкоуровневый контракт, на котором построен каждый
декларативный клиент. Он покрывает весь объектный API плюс многочастные загрузки, принимает `credentials`,
`bucket` и `key` явно в каждом вызове и полезен для операций, которые декларативный контракт не выражает —
пакетное удаление или многочастная загрузка, управляемая вручную.

Модуль не публикует компонент `S3Client`: создайте его из внедряемой фабрики `S3ClientFactory`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends KoraS3ClientModule {

        default S3ClientConfigWithCredentials someS3ClientConfig(Config config, //(1)!
                                                                 ConfigValueMapper<S3ClientConfigWithCredentials> mapper) {
            return mapper.mapOrThrow(config.get("s3client.someClient"));
        }

        default S3Client someS3Client(S3ClientFactory factory, //(2)!
                                      S3ClientConfigWithCredentials config) {
            return factory.create(config);
        }
    }
    ```

    1. Читает ту же структуру `S3ClientConfig`, что читал бы декларативный клиент
    2. Фабрика подключает `HttpClient` и телеметрию из графа

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application : KoraS3ClientModule {

        fun someS3ClientConfig(config: Config, //(1)!
                               mapper: ConfigValueMapper<S3ClientConfigWithCredentials>): S3ClientConfigWithCredentials =
            mapper.mapOrThrow(config.get("s3client.someClient"))

        fun someS3Client(factory: S3ClientFactory, //(2)!
                         config: S3ClientConfigWithCredentials): S3Client =
            factory.create(config)
    }
    ```

    1. Читает ту же структуру `S3ClientConfig`, что читал бы декларативный клиент
    2. Фабрика подключает `HttpClient` и телеметрию из графа

### Операции { #client-imperative-operations }

| Метод                                                                      | Описание                                                                                        |
|----------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------|
| `headObject(credentials, bucket, key[, args])`                             | Метаданные объекта, выбрасывает [`S3ClientNoSuchKeyException`](#not-found-exception), если объекта нет |
| `headObjectOptional(credentials, bucket, key)`                             | Метаданные объекта либо `null`, если объекта нет                                                 |
| `getObject(credentials, bucket, key[, args])`                              | Объект вместе с телом, выбрасывает исключение, если объекта нет                                  |
| `getObjectOptional(credentials, bucket, key)`                              | Объект вместе с телом либо `null`, если объекта нет                                              |
| `putObject(credentials, bucket, key[, args], data, off, len)`              | Загружает диапазон байт массива, возвращает `ETag`                                               |
| `putObject(credentials, bucket, key[, args], contentWriter)`               | Потоковая загрузка `aws-chunked`, возвращает `ETag`                                              |
| `deleteObject(credentials, bucket, key[, args])`                           | Удаляет один объект                                                                              |
| `deleteObjects(credentials, bucket, keys)`                                 | Удаляет до `1000` объектов одним запросом                                                        |
| `listObjectsV2(credentials, bucket, args)`                                 | Одна страница списка                                                                             |
| `listObjectsV2Iterator(credentials, bucket, args)`                         | Ленивый итератор, подгружающий страницы по мере потребления                                      |
| `createMultipartUpload(credentials, bucket, key[, args])`                  | Начинает многочастную загрузку, возвращает её идентификатор                                      |
| `uploadPart(credentials, bucket, key, uploadId, partNumber, ...)`          | Загружает одну часть, возвращает `UploadedPart`                                                  |
| `listParts(credentials, bucket, key, uploadId, ...)`                       | Перечисляет уже загруженные части                                                                |
| `completeMultipartUpload(credentials, bucket, key, uploadId, parts[, args])`| Собирает объект из частей, возвращает `ETag`                                                     |
| `abortMultipartUpload(credentials, bucket, key, uploadId[, args])`         | Прерывает многочастную загрузку и освобождает место, занятое её частями                          |
| `listMultipartUploads(credentials, bucket, args)`                          | Перечисляет начатые, но не завершённые многочастные загрузки                                     |

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeService {

        private final S3Client s3;
        private final S3Credentials credentials;

        public SomeService(S3Client s3, S3ClientConfigWithCredentials config) {
            this.s3 = s3;
            this.credentials = config.credentials();
        }

        public byte[] download(String bucket, String key) throws IOException {
            try (var response = s3.getObject(credentials, bucket, key); //(1)!
                 var body = response.body();
                 var stream = body.asInputStream()) {
                return stream.readAllBytes();
            }
        }

        public void deleteAll(String bucket, List<String> keys) {
            s3.deleteObjects(credentials, bucket, keys); //(2)!
        }
    }
    ```

    1. Выбрасывает `S3ClientNoSuchKeyException`, если объект отсутствует
    2. Выбрасывает [`S3ClientDeleteException`](#delete-exception), если хранилище сообщило о сбоях по отдельным объектам

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService(
        private val s3: S3Client,
        config: S3ClientConfigWithCredentials
    ) {

        private val credentials = config.credentials()

        fun download(bucket: String, key: String): ByteArray {
            s3.getObject(credentials, bucket, key).use { response -> //(1)!
                response.body().asInputStream().use { stream ->
                    return stream.readAllBytes()
                }
            }
        }

        fun deleteAll(bucket: String, keys: List<String>) {
            s3.deleteObjects(credentials, bucket, keys) //(2)!
        }
    }
    ```

    1. Выбрасывает `S3ClientNoSuchKeyException`, если объект отсутствует
    2. Выбрасывает [`S3ClientDeleteException`](#delete-exception), если хранилище сообщило о сбоях по отдельным объектам

### Многочастная загрузка { #client-imperative-multipart }

Многочастная загрузка, управляемая вручную — именно её генерирует декларативный клиент для тела
типа `InputStream`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var uploadId = s3.createMultipartUpload(credentials, bucket, key); //(1)!
    var parts = new ArrayList<UploadedPart>();
    try {
        var buffer = new byte[5 * 1024 * 1024];
        for (int number = 1; ; number++) {
            var read = source.readNBytes(buffer, 0, buffer.length);
            if (read > 0) {
                parts.add(s3.uploadPart(credentials, bucket, key, uploadId, number, buffer, 0, read)); //(2)!
            }
            if (read < buffer.length) {
                break;
            }
        }
        var etag = s3.completeMultipartUpload(credentials, bucket, key, uploadId, parts); //(3)!
    } catch (Exception e) {
        s3.abortMultipartUpload(credentials, bucket, key, uploadId); //(4)!
        throw e;
    }
    ```

    1. Начинает загрузку и возвращает её идентификатор
    2. Нумерация частей начинается с `1`; каждая часть, кроме последней, должна быть не меньше `5MiB`
    3. Собирает объект и возвращает его `ETag`
    4. Освобождает место, занятое уже загруженными частями

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val uploadId = s3.createMultipartUpload(credentials, bucket, key) //(1)!
    val parts = ArrayList<UploadedPart>()
    try {
        val buffer = ByteArray(5 * 1024 * 1024)
        var number = 1
        while (true) {
            val read = source.readNBytes(buffer, 0, buffer.size)
            if (read > 0) {
                parts.add(s3.uploadPart(credentials, bucket, key, uploadId, number, buffer, 0, read)) //(2)!
            }
            if (read < buffer.size) {
                break
            }
            number++
        }
        val etag = s3.completeMultipartUpload(credentials, bucket, key, uploadId, parts) //(3)!
    } catch (e: Exception) {
        s3.abortMultipartUpload(credentials, bucket, key, uploadId) //(4)!
        throw e
    }
    ```

    1. Начинает загрузку и возвращает её идентификатор
    2. Нумерация частей начинается с `1`; каждая часть, кроме последней, должна быть не меньше `5MiB`
    3. Собирает объект и возвращает его `ETag`
    4. Освобождает место, занятое уже загруженными частями

## Исключения { #exceptions }

Если операция клиента завершается неудачей, выбрасывается одно из исключений `S3` из пакета
`io.koraframework.s3.client.kora.exception`. Все они наследуются от абстрактного `S3ClientException`,
который, в свою очередь, расширяет `RuntimeException`, поэтому их обработка необязательна и не проверяется компилятором.

**Иерархия исключений:**

```
RuntimeException
└── S3ClientException
    ├── S3ClientResponseException
    │   └── S3ClientErrorException
    │       └── S3ClientNoSuchKeyException
    ├── S3ClientDeleteException
    └── S3ClientUnknownException
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

        public void call(String key) {
            try {
                client.deleteObject(key);
            } catch (S3ClientNoSuchKeyException e) {
                // Object is missing: e.getErrorCode() is NoSuchKey
            } catch (S3ClientErrorException e) {
                // Storage reported an error document: e.getErrorCode(), e.getErrorMessage(), e.getRequestId()
            } catch (S3ClientResponseException e) {
                // Unexpected HTTP status without a parsable error document: e.getHttpCode()
            } catch (S3ClientException e) {
                // Any other client failure
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

        fun call(key: String) {
            try {
                client.deleteObject(key)
            } catch (e: S3ClientNoSuchKeyException) {
                // Object is missing: e.errorCode is NoSuchKey
            } catch (e: S3ClientErrorException) {
                // Storage reported an error document: e.errorCode, e.errorMessage, e.requestId
            } catch (e: S3ClientResponseException) {
                // Unexpected HTTP status without a parsable error document: e.httpCode
            } catch (e: S3ClientException) {
                // Any other client failure
            }
        }
    }
    ```

### S3ClientNoSuchKeyException { #not-found-exception }

Выбрасывается, когда запрошенный объект не существует, а операция не является
[необязательной](#optional-get). Расширяет `S3ClientErrorException`, поэтому `getErrorCode()` возвращает `NoSuchKey`.

**Рекомендации:**

- Сделайте результат `@S3.Get` или `@S3.Head` [необязательным](#optional-get), если отсутствие объекта — нормальный исход
- Проверьте бакет, полученный через [`@S3.Bucket`](#bucket), и запрошенный ключ
- Помните, что `HEAD`-запрос к отсутствующему **бакету** тоже сообщает `NoSuchKey`, потому что у ответа нет тела

### S3ClientDeleteException { #delete-exception }

Выбрасывается методом `S3Client#deleteObjects`, когда хранилище сообщает о сбоях по отдельным объектам.
Предоставляет список отдельных сбоев:

| Метод                     | Описание                                                       |
|---------------------------|----------------------------------------------------------------|
| `List<Error> getErrors()` | Сбои по каждому объекту, каждый с `key()`, `code()`, `message()` |

**Рекомендации:**

- Изучите `getErrors()`, чтобы определить, какие объекты не удалось обработать и почему
- Повторите неудавшиеся ключи отдельно, если сбой временный

### S3ClientErrorException { #error-exception }

Выбрасывается, когда хранилище ответило статусом ошибки и разбираемым документом ошибки `S3`.

| Метод                      | Описание                                             |
|----------------------------|------------------------------------------------------|
| `int getHttpCode()`        | Код статуса `HTTP` ответа                             |
| `String getErrorCode()`    | Код ошибки хранилища (например, `AccessDenied`)       |
| `String getErrorMessage()` | Сообщение об ошибке хранилища                         |
| `String getRequestId()`    | Идентификатор запроса, сообщённый хранилищем, может быть `null` |

**Рекомендации:**

- Логируйте `getErrorCode()`, `getErrorMessage()` и `getRequestId()` для диагностики — именно идентификатор запроса нужен операторам хранилища
- `SignatureDoesNotMatch` и `InvalidAccessKeyId` означают, что неверны [учётные данные](#credentials) или `region`

### S3ClientResponseException { #response-exception }

Базовый класс для всех сбоев, несущих статус `HTTP`: хранилище ответило, но либо неожиданным статусом,
либо телом, которое не является документом ошибки `S3`.

| Метод               | Описание                           |
|---------------------|------------------------------------|
| `int getHttpCode()` | Код статуса `HTTP` ответа           |

**Рекомендации:**

- `403` обычно означает неверные учётные данные или отсутствующую политику
- Включите [логирование](#configuration) клиента и телеметрию `HTTP`-клиента, чтобы изучить нижележащие запрос и ответ

### S3ClientUnknownException { #unknown-exception }

Выбрасывается, когда операция завершилась неудачей до или вне обмена по `HTTP` — `IOException` при чтении
загружаемого потока, сбой транспорта, ошибка разбора XML. Исходный сбой всегда доступен как `cause`.

### S3ClientException { #base-exception }

Абстрактный базовый класс всех исключений выше. Ловите его последней веткой `catch`, чтобы единообразно
обработать любую ошибку хранилища или клиента.

## Клиент AWS SDK { #aws }

Артефакт `s3-client-aws` — это тонкая интеграция вокруг
[AWS SDK for Java v2](https://github.com/aws/aws-sdk-java-v2). Он публикует собственный клиент SDK
`software.amazon.awssdk.services.s3.S3Client` как компонент графа, настраивает его из конфигурации Kora
и направляет его `HTTP`-трафик через `HttpClient` Kora, чтобы таймауты и телеметрия оставались
согласованными с остальным приложением.

В нём **нет аннотаций `@S3` и нет моделей Kora S3** — работа с этим артефактом означает работу
с API AWS SDK. Используйте его для всего, что не покрывает декларативный контракт: администрирование
бакетов, копирование объектов, предподписанные URL, управление ACL и политиками, пакетное удаление.

### Подключение { #dependency-2 }

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "io.koraframework:s3-client-aws"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends AwsS3ClientModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("io.koraframework:s3-client-aws")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : AwsS3ClientModule
    ```

Обратите внимание, что группа здесь `io.koraframework`, а не `io.koraframework.experimental` — этот
артефакт не является экспериментальным модулем. Требуется добавить любой модуль
[HTTP-клиента](http-client.md): собственные транспорты SDK `apache-client` и `netty-nio-client`
исключены, а Kora предоставляет реализацию `SdkHttpClient` поверх `HttpClient` из графа.

### Конфигурация { #configuration-2 }

Конфигурация читается по пути `s3client.aws`. Основные параметры:

===! ":material-code-json: `Hocon`"

    ```javascript
    s3client.aws {
        url = "http://localhost:9000" //(1)!
        credentials {
            accessKey = "someKey" //(2)!
            secretKey = "someSecret" //(3)!
        }
        region = "aws-global" //(4)!
    }
    ```

    1.  `URL` хранилища `S3` (`обязательный`, по умолчанию не указано)
    2.  Ключ доступа к `S3` (`обязательный`, по умолчанию не указано)
    3.  Секрет доступа к `S3` (`обязательный`, по умолчанию не указано)
    4.  Регион хранилища `S3` (по умолчанию: `aws-global`)

=== ":simple-yaml: `YAML`"

    ```yaml
    s3client:
      aws:
        url: "http://localhost:9000" #(1)!
        credentials:
          accessKey: "someKey" #(2)!
          secretKey: "someSecret" #(3)!
        region: "aws-global" #(4)!
    ```

    1.  `URL` хранилища `S3` (`обязательный`, по умолчанию не указано)
    2.  Ключ доступа к `S3` (`обязательный`, по умолчанию не указано)
    3.  Секрет доступа к `S3` (`обязательный`, по умолчанию не указано)
    4.  Регион хранилища `S3` (по умолчанию: `aws-global`)

??? note "Полная конфигурация"

    Полная конфигурация описана в классе `AwsS3Config` (указаны примеры значений или значения по умолчанию):

    ===! ":material-code-json: `Hocon`"

        ```javascript
        s3client.aws {
            url = "http://localhost:9000" //(1)!
            credentials {
                accessKey = "someKey" //(2)!
                secretKey = "someSecret" //(3)!
            }
            region = "aws-global" //(4)!
            addressStyle = "PATH" //(5)!
            requestTimeout = "45s" //(6)!
            checksumCalculationRequest = "WHEN_REQUIRED" //(7)!
            checksumValidationResponse = "WHEN_REQUIRED" //(8)!
            chunkedEncodingEnabled = true //(9)!
            telemetry {
                logging {
                    enabled = false //(10)!
                }
                metrics {
                    enabled = false //(11)!
                    slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(12)!
                    tags = { // (13)!
                        "key1" = "value1"
                        "key2" = "value2"
                    }
                }
                tracing {
                    enabled = true //(14)!
                    attributes = { // (15)!
                        "key1" = "value1"
                        "key2" = "value2"
                    }
                }
            }
        }
        ```

        1.  `URL` хранилища `S3`, передаётся в SDK как переопределение endpoint (`обязательный`, по умолчанию не указано)
        2.  Ключ доступа к `S3` (`обязательный`, по умолчанию не указано)
        3.  Секрет доступа к `S3` (`обязательный`, по умолчанию не указано)
        4.  Регион хранилища `S3` (по умолчанию: `aws-global`)
        5.  Стиль доступа к объектам, может иметь значения `PATH` или `VIRTUAL_HOSTED` (по умолчанию: `PATH`)
        6.  Максимальное время выполнения операции, применяется к нижележащему `HTTP`-запросу (по умолчанию: `45s`)
        7.  Когда вычисляются контрольные суммы запроса, может иметь значения `WHEN_SUPPORTED` или `WHEN_REQUIRED` (по умолчанию: `WHEN_REQUIRED`)
        8.  Когда проверяются контрольные суммы ответа, может иметь значения `WHEN_SUPPORTED` или `WHEN_REQUIRED` (по умолчанию: `WHEN_REQUIRED`)
        9.  Использовать ли частичное (chunked) кодирование при подписании данных объекта во время загрузки (по умолчанию: `true`)
        10. Включает логирование модуля (по умолчанию: `false`)
        11. Включает метрики модуля (по умолчанию: `false`)
        12. Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
        13. Настройка тегов метрик (по умолчанию: `{}`)
        14. Включает трассировку модуля (по умолчанию: `true`)
        15. Настройка атрибутов трассировки (по умолчанию: `{}`)

    === ":simple-yaml: `YAML`"

        ```yaml
        s3client:
          aws:
            url: "http://localhost:9000" #(1)!
            credentials:
              accessKey: "someKey" #(2)!
              secretKey: "someSecret" #(3)!
            region: "aws-global" #(4)!
            addressStyle: "PATH" #(5)!
            requestTimeout: "45s" #(6)!
            checksumCalculationRequest: "WHEN_REQUIRED" #(7)!
            checksumValidationResponse: "WHEN_REQUIRED" #(8)!
            chunkedEncodingEnabled: true #(9)!
            telemetry:
              logging:
                enabled: false #(10)!
              metrics:
                enabled: false #(11)!
                slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(12)!
                tags: #(13)!
                  key1: value1
                  key2: value2
              tracing:
                enabled: true #(14)!
                attributes: #(15)!
                  key1: value1
                  key2: value2
        ```

        1.  `URL` хранилища `S3`, передаётся в SDK как переопределение endpoint (`обязательный`, по умолчанию не указано)
        2.  Ключ доступа к `S3` (`обязательный`, по умолчанию не указано)
        3.  Секрет доступа к `S3` (`обязательный`, по умолчанию не указано)
        4.  Регион хранилища `S3` (по умолчанию: `aws-global`)
        5.  Стиль доступа к объектам, может иметь значения `PATH` или `VIRTUAL_HOSTED` (по умолчанию: `PATH`)
        6.  Максимальное время выполнения операции, применяется к нижележащему `HTTP`-запросу (по умолчанию: `45s`)
        7.  Когда вычисляются контрольные суммы запроса, может иметь значения `WHEN_SUPPORTED` или `WHEN_REQUIRED` (по умолчанию: `WHEN_REQUIRED`)
        8.  Когда проверяются контрольные суммы ответа, может иметь значения `WHEN_SUPPORTED` или `WHEN_REQUIRED` (по умолчанию: `WHEN_REQUIRED`)
        9.  Использовать ли частичное (chunked) кодирование при подписании данных объекта во время загрузки (по умолчанию: `true`)
        10. Включает логирование модуля (по умолчанию: `false`)
        11. Включает метрики модуля (по умолчанию: `false`)
        12. Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
        13. Настройка тегов метрик (по умолчанию: `{}`)
        14. Включает трассировку модуля (по умолчанию: `true`)
        15. Настройка атрибутов трассировки (по умолчанию: `{}`)

Имя бакета не входит в `AwsS3Config`: SDK принимает его в каждом запросе, поэтому объявите его
в собственном интерфейсе [`@ConfigSource`](config.md).

### Использование { #aws-usage }

Клиент SDK внедряется напрямую, без тега:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class AwsS3Service {

        private final S3Client s3Client; //(1)!
        private final String bucket;

        public AwsS3Service(S3Client s3Client, S3Config config) {
            this.s3Client = s3Client;
            this.bucket = config.bucket();
        }

        public PutObjectResponse putObject(String key, byte[] value) {
            return s3Client.putObject(r -> r.bucket(bucket).key(key), RequestBody.fromBytes(value));
        }

        public ResponseInputStream<GetObjectResponse> getObject(String key) {
            return s3Client.getObject(r -> r.bucket(bucket).key(key));
        }

        public ListObjectsV2Response listObjects(String prefix) {
            return s3Client.listObjectsV2(r -> r.bucket(bucket).prefix(prefix).maxKeys(50));
        }

        public DeleteObjectsResponse deleteObjects(List<String> keys) { //(2)!
            var identifiers = keys.stream()
                    .map(key -> ObjectIdentifier.builder().key(key).build())
                    .toList();

            return s3Client.deleteObjects(r -> r.bucket(bucket).delete(d -> d.objects(identifiers)));
        }
    }
    ```

    1. `software.amazon.awssdk.services.s3.S3Client`, клиент AWS SDK
    2. Пакетное удаление, которое [декларативный клиент](#delete-file) не генерирует

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class AwsS3Service(
        private val s3Client: S3Client, //(1)!
        config: S3Config
    ) {

        private val bucket: String = config.bucket()

        fun putObject(key: String, value: ByteArray): PutObjectResponse =
            s3Client.putObject({ it.bucket(bucket).key(key) }, RequestBody.fromBytes(value))

        fun getObject(key: String): ResponseInputStream<GetObjectResponse> =
            s3Client.getObject { it.bucket(bucket).key(key) }

        fun listObjects(prefix: String): ListObjectsV2Response =
            s3Client.listObjectsV2 { it.bucket(bucket).prefix(prefix).maxKeys(50) }

        fun deleteObjects(keys: List<String>): DeleteObjectsResponse { //(2)!
            val identifiers = keys.map { ObjectIdentifier.builder().key(it).build() }
            return s3Client.deleteObjects { r -> r.bucket(bucket).delete { d -> d.objects(identifiers) } }
        }
    }
    ```

    1. `software.amazon.awssdk.services.s3.S3Client`, клиент AWS SDK
    2. Пакетное удаление, которое [декларативный клиент](#delete-file) не генерирует

Об ошибках сообщает собственная иерархия исключений SDK — `NoSuchKeyException`,
`NoSuchBucketException`, `S3Exception` — а не [исключения Kora `S3`](#exceptions).

Пользовательское поведение SDK добавляется компонентами `ExecutionInterceptor`: каждый
`software.amazon.awssdk.core.interceptor.ExecutionInterceptor`, опубликованный под
`@Tag(Tag.Factory.class)`, регистрируется на клиенте рядом с собственным перехватчиком телеметрии Kora.

## Использование обоих артефактов { #both }

Оба артефакта могут жить в одном приложении: они занимают разные пакеты и разные секции конфигурации,
поэтому согласовывать нечего.

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    implementation "io.koraframework:s3-client-aws"
    implementation "io.koraframework.experimental:s3-client-kora"
    ```

    ```java
    @KoraApp
    public interface Application extends AwsS3ClientModule, KoraS3ClientModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```groovy
    implementation("io.koraframework:s3-client-aws")
    implementation("io.koraframework.experimental:s3-client-kora")
    ```

    ```kotlin
    @KoraApp
    interface Application : AwsS3ClientModule, KoraS3ClientModule
    ```

===! ":material-code-json: `Hocon`"

    ```javascript
    s3client.aws { //(1)!
        url = ${S3_URL}
        credentials {
            accessKey = ${S3_ACCESS_KEY}
            secretKey = ${S3_SECRET_KEY}
        }
    }

    s3client.uploads { //(2)!
        endpoint = ${S3_URL}
        bucket = "uploads"
        credentials {
            accessKey = ${S3_ACCESS_KEY}
            secretKey = ${S3_SECRET_KEY}
        }
    }
    ```

    1.  Фиксированный путь [клиента AWS SDK](#aws)
    2.  Путь, объявленный в `@S3.Client("s3client.uploads")` [декларативного клиента](#client-declarative)

=== ":simple-yaml: `YAML`"

    ```yaml
    s3client:
      aws: #(1)!
        url: ${S3_URL}
        credentials:
          accessKey: ${S3_ACCESS_KEY}
          secretKey: ${S3_SECRET_KEY}

      uploads: #(2)!
        endpoint: ${S3_URL}
        bucket: "uploads"
        credentials:
          accessKey: ${S3_ACCESS_KEY}
          secretKey: ${S3_SECRET_KEY}
    ```

    1.  Фиксированный путь [клиента AWS SDK](#aws)
    2.  Путь, объявленный в `@S3.Client("s3client.uploads")` [декларативного клиента](#client-declarative)

### Администрирование бакетов { #bucket-administration }

Создание бакета или проверка его существования не входят в контракт `@S3`, поэтому выполняются через
клиент AWS SDK. Имя бакета из `@S3.Bucket` попадает в сгенерированный класс, а не в компонент, поэтому
инициализатор читает тот же путь конфигурации самостоятельно:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @ConfigSource("s3client.uploads")
    public interface S3UploadsConfig {

        String bucket();
    }
    ```

    ```java
    @Root //(1)!
    @Component
    public final class S3BucketInitializer implements Lifecycle {

        private final S3Client s3Client; //(2)!
        private final S3UploadsConfig config;

        public S3BucketInitializer(S3Client s3Client, S3UploadsConfig config) {
            this.s3Client = s3Client;
            this.config = config;
        }

        @Override
        public void init() {
            var bucket = this.config.bucket();
            try {
                this.s3Client.headBucket(HeadBucketRequest.builder().bucket(bucket).build());
            } catch (NoSuchBucketException e) {
                this.s3Client.createBucket(CreateBucketRequest.builder().bucket(bucket).build());
            }
        }

        @Override
        public void release() {}
    }
    ```

    1. Обязательно: от этого компонента никто не зависит, поэтому без `@Root` он будет выброшен из графа
    2. `software.amazon.awssdk.services.s3.S3Client`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @ConfigSource("s3client.uploads")
    interface S3UploadsConfig {

        fun bucket(): String
    }
    ```

    ```kotlin
    @Root //(1)!
    @Component
    class S3BucketInitializer(
        private val s3Client: S3Client, //(2)!
        private val config: S3UploadsConfig
    ) : Lifecycle {

        override fun init() {
            val bucket = config.bucket()
            try {
                s3Client.headBucket(HeadBucketRequest.builder().bucket(bucket).build())
            } catch (e: NoSuchBucketException) {
                s3Client.createBucket(CreateBucketRequest.builder().bucket(bucket).build())
            }
        }

        override fun release() {}
    }
    ```

    1. Обязательно: от этого компонента никто не зависит, поэтому без `@Root` он будет выброшен из графа
    2. `software.amazon.awssdk.services.s3.S3Client`

!!! warning "Компонент Lifecycle, от которого никто не зависит, выбрасывается"

    Kora собирает только достижимую часть графа. Компонент, который лишь подготавливает внешнее состояние
    и ни от чего не является зависимостью, удаляется вместе со всем, что он за собой тянул,
    и это проявляется как ошибка сборки вида
    `interface software.amazon.awssdk.services.s3.S3Client wasn't found in graph`.
    Пометьте его как [`@Root`](container.md#root-component), чтобы он остался.

## Тестирование { #testing }

Декларативные клиенты можно тестировать с помощью [@KoraAppTest](junit5.md) вместе с реальным
`S3`-совместимым хранилищем, запущенным в контейнере [Testcontainers](https://java.testcontainers.org/) —
удобный вариант `Minio`. Параметры подключения к хранилищу передаются в конфигурацию приложения
через системные свойства:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @TestcontainersMinio(
            mode = ContainerMode.PER_RUN,
            bucket = @Bucket(value = SomeClientTests.BUCKET, create = Bucket.Mode.PER_METHOD, drop = Bucket.Mode.PER_METHOD))
    @KoraAppTest(Application.class)
    class SomeClientTests implements KoraAppTestConfigModifier {

        static final String BUCKET = "simple";

        @ConnectionMinio
        private MinioConnection minioConnection;

        @TestComponent
        private SomeClient client;

        @Override
        public KoraConfigModification config() {
            return KoraConfigModification
                    .ofSystemProperty("S3_URL", minioConnection.params().uri().toString())
                    .withSystemProperty("S3_ACCESS_KEY", minioConnection.params().accessKey())
                    .withSystemProperty("S3_SECRET_KEY", minioConnection.params().secretKey())
                    .withSystemProperty("S3_BUCKET", BUCKET);
        }

        @Test
        void putAndGet() throws IOException {
            var value = "value".getBytes(StandardCharsets.UTF_8);
            client.putObject("k1", value);

            try (var found = client.getObject("k1"); var body = found.body().asInputStream()) {
                assertArrayEquals(value, body.readAllBytes());
            }
        }

        @Test
        void getMissing() {
            assertThrows(S3ClientNoSuchKeyException.class, () -> client.getObject("k2"));
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @TestcontainersMinio(
        mode = ContainerMode.PER_RUN,
        bucket = Bucket(value = [SomeClientTests.BUCKET], create = Bucket.Mode.PER_METHOD, drop = Bucket.Mode.PER_METHOD))
    @KoraAppTest(Application::class)
    class SomeClientTests : KoraAppTestConfigModifier {

        @ConnectionMinio
        lateinit var minioConnection: MinioConnection

        @TestComponent
        lateinit var client: SomeClient

        override fun config(): KoraConfigModification = KoraConfigModification
            .ofSystemProperty("S3_URL", minioConnection.params().uri().toString())
            .withSystemProperty("S3_ACCESS_KEY", minioConnection.params().accessKey())
            .withSystemProperty("S3_SECRET_KEY", minioConnection.params().secretKey())
            .withSystemProperty("S3_BUCKET", BUCKET)

        @Test
        fun putAndGet() {
            val value = "value".toByteArray(StandardCharsets.UTF_8)
            client.putObject("k1", value)

            client.getObject("k1").use { found ->
                found.body().asInputStream().use { body ->
                    assertArrayEquals(value, body.readAllBytes())
                }
            }
        }

        @Test
        fun getMissing() {
            assertThrows(S3ClientNoSuchKeyException::class.java) { client.getObject("k2") }
        }

        companion object {
            const val BUCKET = "simple"
        }
    }
    ```

Конфигурация приложения, которую использует такой тест, читает эти системные свойства:

===! ":material-code-json: `Hocon`"

    ```javascript
    s3client.someClient {
        endpoint = ${S3_URL}
        bucket = ${S3_BUCKET}
        credentials {
            accessKey = ${S3_ACCESS_KEY}
            secretKey = ${S3_SECRET_KEY}
        }
    }
    ```

=== ":simple-yaml: `YAML`"

    ```yaml
    s3client:
      someClient:
        endpoint: ${S3_URL}
        bucket: ${S3_BUCKET}
        credentials:
          accessKey: ${S3_ACCESS_KEY}
          secretKey: ${S3_SECRET_KEY}
    ```
