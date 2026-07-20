---
description: "Explains Kora S3 clients for AWS and Minio, declarative and imperative clients, file operations, metadata, key templates, and exception handling. Use when working with @S3.Client, @S3.Get, @S3.List, @S3.Put, @S3.Delete, S3ClientModule, AwsS3Client, MinioS3Client."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora S3 clients for AWS and Minio, declarative and imperative clients, file operations, metadata, key templates, and exception handling; key triggers include @S3.Client, @S3.Get, @S3.List, @S3.Put, @S3.Delete, S3ClientModule, AwsS3Client, MinioS3Client."
---

??? warning "Экспериментальный модуль"

    **Экспериментальный** модуль полностью работает и протестирован, но требует дополнительной апробации и аналитики использования,
    поэтому API потенциально может претерпеть незначительные изменения до того, как станет полностью стабильным.

Модуль предоставляет слой абстракции для работы с [S3-совместимым объектным хранилищем](https://aws.amazon.com/s3/faqs/):
можно создавать декларативные `S3`-клиенты с помощью аннотаций либо внедрять готовые к использованию императивные клиенты.
Декларативный клиент удобен для типовых операций с объектами и ключами, тогда как императивный клиент полезен, когда операциями
нужно управлять напрямую в коде.

Если нужен пошаговый разбор перед справочным описанием, смотрите [S3](../guides/s3.md).

## AWS { #aws }

Реализация `S3`-клиента основана на [библиотеке AWS](https://github.com/aws/aws-sdk-java-v2).

Компоненты, доступные для внедрения:

- Императивные [Kora S3-клиенты](#client-imperative)
- `S3Client` синхронный AWS S3-клиент
- `S3AsyncClient` асинхронный AWS S3-клиент
- `S3AsyncClient` с тегом `@Tag(MultipartUpload.class)` асинхронный AWS S3-клиент для пакетной загрузки

### Подключение { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora.experimental:s3-client-aws"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends AwsS3ClientModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora.experimental:s3-client-aws")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : AwsS3ClientModule
    ```

Требуется добавить любой модуль [HTTP-клиента](http-client.md).

### Конфигурация { #configuration }

Основные параметры конфигурации S3 клиента:

===! ":material-code-json: `HOCON`"

    ```javascript
    s3client {
        url = "http://localhost:9000" //(1)!
        accessKey = "someKey" //(2)!
        secretKey = "someSecret" //(3)!
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
      url: "http://localhost:9000" #(1)!
      accessKey: "someKey" #(2)!
      secretKey: "someSecret" #(3)!
      region: "aws-global" #(4)!
    ```

    1.  `URL` хранилища `S3` (`обязательный`, по умолчанию не указано)
    2.  Ключ доступа к `S3` (`обязательный`, по умолчанию не указано)
    3.  Секрет доступа к `S3` (`обязательный`, по умолчанию не указано)
    4.  Регион хранилища `S3` (по умолчанию: `aws-global`)

??? note "Полная конфигурация"

    Пример полной конфигурации, описанной в классах `AwsS3ClientConfig` и `S3Config` (указаны примеры значений или значения по умолчанию):

    ===! ":material-code-json: `HOCON`"

        ```javascript
        s3client {
            aws {
                addressStyle = "PATH" //(1)!
                requestTimeout = "45s" //(2)!
                checksumValidationEnabled = false //(3)!
                chunkedEncodingEnabled = true //(4)!
                upload {
                    bufferSize = "32MiB" //(5)!
                    partSize = "8MiB" //(6)!
                }
            }

            url = "http://localhost:9000" //(7)!
            accessKey = "someKey" //(8)!
            secretKey = "someSecret" //(9)!
            region = "aws-global" //(10)!
            telemetry {
                logging {
                    enabled = false //(11)!
                }
                metrics {
                    enabled = true //(12)!
                    slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(13)!
                    tags = { // (14)!
                        "key1" = "value1"
                        "key2" = "value2"
                    }
                }
                tracing {
                    enabled = true //(15)!
                    attributes = { // (16)!
                        "key1" = "value1"
                        "key2" = "value2"
                    }
                }
            }
        }
        ```

        1.  Стиль доступа к объектам, может иметь значения `PATH` или `VIRTUAL_HOSTED` (по умолчанию: `PATH`)
        2.  Максимальное время выполнения операции (по умолчанию: `45s`)
        3.  Проверять ли [контрольную сумму MD5 перед загрузкой и при получении](https://sdk.amazonaws.com/java/api/latest/software/amazon/awssdk/services/s3/S3Configuration.Builder.html#checksumValidationEnabled(java.lang.Boolean)) из `AWS` (по умолчанию: `false`)
        4.  Использовать ли частичное (chunked) кодирование при подписании данных файла во время загрузки в `AWS` (по умолчанию: `true`)
        5.  Максимальный размер буфера для загрузки файлов (по умолчанию: `32MiB`)
        6.  Максимальный размер части файла при загрузке одного файла (по умолчанию: `8MiB`)
        7.  `URL` хранилища `S3` (`обязательный`, по умолчанию не указано)
        8.  Ключ доступа к `S3` (`обязательный`, по умолчанию не указано)
        9.  Секрет доступа к `S3` (`обязательный`, по умолчанию не указано)
        10. Регион хранилища `S3` (по умолчанию: `aws-global`)
        11. Включает логирование модуля (по умолчанию: `false`)
        12. Включает метрики модуля (по умолчанию: `true`)
        13. Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
        14. Настройка тегов метрик (по умолчанию: `{}`)
        15. Включает трассировку модуля (по умолчанию: `true`)
        16. Настройка атрибутов трассировки (по умолчанию: `{}`)

    === ":simple-yaml: `YAML`"

        ```yaml
        s3client:
          aws:
            addressStyle: "PATH" #(1)!
            requestTimeout: "45s" #(2)!
            checksumValidationEnabled: false #(3)!
            chunkedEncodingEnabled: true #(4)!
            upload:
              bufferSize: "32MiB" #(5)!
              partSize: "8MiB" #(6)!

          url: "http://localhost:9000" #(7)!
          accessKey: "someKey" #(8)!
          secretKey: "someSecret" #(9)!
          region: "aws-global" #(10)!
          telemetry:
            logging:
              enabled: false #(11)!
            metrics:
              enabled: true #(12)!
              slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(13)!
              tags: #(14)!
                key1: value1
                key2: value2
            tracing:
              enabled: true #(15)!
              attributes: #(16)!
                key1: value1
                key2: value2
        ```

        1.  Стиль доступа к объектам, может иметь значения `PATH` или `VIRTUAL_HOSTED` (по умолчанию: `PATH`)
        2.  Максимальное время выполнения операции (по умолчанию: `45s`)
        3.  Проверять ли [контрольную сумму MD5 перед загрузкой и при получении](https://sdk.amazonaws.com/java/api/latest/software/amazon/awssdk/services/s3/S3Configuration.Builder.html#checksumValidationEnabled(java.lang.Boolean)) из `AWS` (по умолчанию: `false`)
        4.  Использовать ли частичное (chunked) кодирование при подписании данных файла во время загрузки в `AWS` (по умолчанию: `true`)
        5.  Максимальный размер буфера для загрузки файлов (по умолчанию: `32MiB`)
        6.  Максимальный размер части файла при загрузке одного файла (по умолчанию: `8MiB`)
        7.  `URL` хранилища `S3` (`обязательный`, по умолчанию не указано)
        8.  Ключ доступа к `S3` (`обязательный`, по умолчанию не указано)
        9.  Секрет доступа к `S3` (`обязательный`, по умолчанию не указано)
        10. Регион хранилища `S3` (по умолчанию: `aws-global`)
        11. Включает логирование модуля (по умолчанию: `false`)
        12. Включает метрики модуля (по умолчанию: `true`)
        13. Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
        14. Настройка тегов метрик (по умолчанию: `{}`)
        15. Включает трассировку модуля (по умолчанию: `true`)
        16. Настройка атрибутов трассировки (по умолчанию: `{}`)

Метрики модуля описаны в разделе [Справочник по метрикам](metrics.md#s3-client).

### Формат ответа { #response-format }

При использовании модуля `AWS` можно возвращать специальные форматы ответа, специфичные для библиотеки `AWS`:

| Операция                                | Формат ответа                                                                                                                                                                                                                                                                |
|-----------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| [Получение файла](#get-file)            | [GetObjectResponse](https://sdk.amazonaws.com/java/api/latest/software/amazon/awssdk/services/s3/model/GetObjectResponse.html) / [ResponseInputStream<GetObjectResponse>](https://sdk.amazonaws.com/java/api/latest/software/amazon/awssdk/core/ResponseInputStream.html)     |
| [Получение метаданных файла](#metadata) | [HeadObjectResponse](https://sdk.amazonaws.com/java/api/latest/software/amazon/awssdk/services/s3/model/HeadObjectResponse.html)                                                                                                                                              |
| [Получение списка файлов](#list-files)  | [ListObjectsV2Response](https://sdk.amazonaws.com/java/api/latest/software/amazon/awssdk/services/s3/model/ListObjectsV2Response.html)                                                                                                                                        |
| [Добавление файла](#add-file)           | [PutObjectResponse](https://sdk.amazonaws.com/java/api/latest/software/amazon/awssdk/services/s3/model/PutObjectResponse.html)                                                                                                                                                |
| [Удаление файла](#delete-file)          | [DeleteObjectResponse](https://sdk.amazonaws.com/java/api/latest/software/amazon/awssdk/services/s3/model/DeleteObjectResponse.html) / [DeleteObjectsResponse](https://sdk.amazonaws.com/java/api/latest/software/amazon/awssdk/services/s3/model/DeleteObjectsResponse.html) |

Для операций `@S3.Get`, получающих объект или метаданные, отсутствие объекта можно описать в типе ответа.
В `Java` поддерживаются `Optional<S3Object>`, `Optional<S3ObjectMeta>`, `Optional<GetObjectResponse>`,
`Optional<ResponseInputStream<GetObjectResponse>>` и `Optional<HeadObjectResponse>`.
В `Kotlin` для этого используются nullable-типы ответа: `S3Object?`, `S3ObjectMeta?`, `GetObjectResponse?`,
`ResponseInputStream<GetObjectResponse>?` и `HeadObjectResponse?`.

## Minio { #minio }

Реализация `S3`-клиента основана на библиотеке [Minio](https://github.com/minio/minio-java).
Учитывайте, что реализация использует [OkHttp](https://github.com/square/okhttp), написанную на `Kotlin`, и её зависимости.

Компоненты, доступные для внедрения:

- Императивные [Kora S3-клиенты](#client-imperative)
- `MinioClient` синхронный Minio S3-клиент
- `MinioAsyncClient` асинхронный Minio S3-клиент

### Подключение { #dependency-2 }

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora.experimental:s3-client-minio"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends MinioS3ClientModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora.experimental:s3-client-minio")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : MinioS3ClientModule
    ```

Можно добавить зависимость [модуля OkHttp](http-client.md#okhttp), иначе будет автоматически создан стандартный HTTP-клиент.

### Конфигурация { #configuration-2 }

Основные параметры конфигурации Minio S3 клиента:

===! ":material-code-json: `HOCON`"

    ```javascript
    s3client {
        url = "http://localhost:9000" //(1)!
        accessKey = "someKey" //(2)!
        secretKey = "someSecret" //(3)!
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
      url: "http://localhost:9000" #(1)!
      accessKey: "someKey" #(2)!
      secretKey: "someSecret" #(3)!
      region: "aws-global" #(4)!
    ```

    1.  `URL` хранилища `S3` (`обязательный`, по умолчанию не указано)
    2.  Ключ доступа к `S3` (`обязательный`, по умолчанию не указано)
    3.  Секрет доступа к `S3` (`обязательный`, по умолчанию не указано)
    4.  Регион хранилища `S3` (по умолчанию: `aws-global`)

??? note "Полная конфигурация"

    Пример полной конфигурации, описанной в классах `MinioS3ClientConfig` и `S3Config` (указаны примеры значений или значения по умолчанию):

    ===! ":material-code-json: `HOCON`"

        ```javascript
        s3client {
            minio {
                addressStyle = "PATH" //(1)!
                requestTimeout = "45s" //(2)!
                upload {
                    partSize = "8MiB" //(3)!
                }
            }

            url = "http://localhost:9000" //(4)!
            accessKey = "someKey" //(5)!
            secretKey = "someSecret" //(6)!
            region = "aws-global" //(7)!
            telemetry {
                logging {
                    enabled = false //(8)!
                }
                metrics {
                    enabled = true //(9)!
                    slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(10)!
                    tags = { // (11)!
                        "key1" = "value1"
                        "key2" = "value2"
                    }
                }
                tracing {
                    enabled = true //(12)!
                    attributes = { // (13)!
                        "key1" = "value1"
                        "key2" = "value2"
                    }
                }
            }
        }
        ```

        1. Стиль доступа к объектам, может иметь значения `PATH` или `VIRTUAL_HOSTED` (по умолчанию: `PATH`)
        2. Максимальное время выполнения операции (по умолчанию: `45s`)
        3. Максимальный размер части файла при загрузке одного файла (по умолчанию: `8MiB`)
        4. `URL` хранилища `S3` (`обязательный`, по умолчанию не указано)
        5. Ключ доступа к `S3` (`обязательный`, по умолчанию не указано)
        6. Секрет доступа к `S3` (`обязательный`, по умолчанию не указано)
        7. Регион хранилища `S3` (по умолчанию: `aws-global`)
        8. Включает логирование модуля (по умолчанию: `false`)
        9. Включает метрики модуля (по умолчанию: `true`)
        10. Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
        11. Настройка тегов метрик (по умолчанию: `{}`)
        12. Включает трассировку модуля (по умолчанию: `true`)
        13. Настройка атрибутов трассировки (по умолчанию: `{}`)

    === ":simple-yaml: `YAML`"

        ```yaml
        s3client:
          minio:
            addressStyle: "PATH" #(1)!
            requestTimeout: "45s" #(2)!
            upload:
              partSize: "8MiB" #(3)!

          url: "http://localhost:9000" #(4)!
          accessKey: "someKey" #(5)!
          secretKey: "someSecret" #(6)!
          region: "aws-global" #(7)!
          telemetry:
            logging:
              enabled: false #(8)!
            metrics:
              enabled: true #(9)!
              slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(10)!
              tags: #(11)!
                key1: value1
                key2: value2
            tracing:
              enabled: true #(12)!
              attributes: #(13)!
                key1: value1
                key2: value2
        ```

        1. Стиль доступа к объектам, может иметь значения `PATH` или `VIRTUAL_HOSTED` (по умолчанию: `PATH`)
        2. Максимальное время выполнения операции (по умолчанию: `45s`)
        3. Максимальный размер части файла при загрузке одного файла (по умолчанию: `8MiB`)
        4. `URL` хранилища `S3` (`обязательный`, по умолчанию не указано)
        5. Ключ доступа к `S3` (`обязательный`, по умолчанию не указано)
        6. Секрет доступа к `S3` (`обязательный`, по умолчанию не указано)
        7. Регион хранилища `S3` (по умолчанию: `aws-global`)
        8. Включает логирование модуля (по умолчанию: `false`)
        9. Включает метрики модуля (по умолчанию: `true`)
        10. Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
        11. Настройка тегов метрик (по умолчанию: `{}`)
        12. Включает трассировку модуля (по умолчанию: `true`)
        13. Настройка атрибутов трассировки (по умолчанию: `{}`)

## Декларативный клиент { #client-declarative }

Для создания декларативного клиента предлагается использовать специальные аннотации:

* `@S3.Client` - указывает, что интерфейс является декларативным S3-клиентом
* `@S3.Get` - указывает, что метод выполняет [операцию получения файла/метаданных](#get-file)
* `@S3.List` - указывает, что метод выполняет [операцию получения списка файлов/метаданных](#list-files)
* `@S3.Put` - указывает, что метод выполняет [операцию добавления файла](#add-file)
* `@S3.Delete` - указывает, что метод выполняет [операцию удаления файла](#delete-file)

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client
    public interface SomeClient {

        @S3.Get 
        S3Object operation(String key); 
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client
    interface SomeClient {

        @S3.Get 
        fun operation(key: String): S3Object
    }
    ```

### Конфигурация клиента { #client-configuration }

Конфигурация конкретной реализации `@S3.Client`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient") //(1)!
    public interface SomeClient {

        @S3.Get 
        S3Object operation(String key); 
    }
    ```

    1. Путь к конфигурации данного конкретного клиента

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient") //(1)!
    interface SomeClient {

        @S3.Get 
        fun operation(key: String): S3Object
    }
    ```

    1. Путь к конфигурации данного конкретного клиента

`@S3.Client` без аргументов эквивалентна `@S3.Client("")`: значение `value` аннотации пустое,
и `S3ClientConfig` будет считана из пустого пути через `Config.get("")`.
На практике обычно лучше указывать явный путь, например `@S3.Client("s3client.someClient")`,
чтобы конфигурация `bucket` была отделена от других клиентов.

Конфигурация для случая пути `s3client.someClient`, описанная в классе `S3ClientConfig`:

===! ":material-code-json: `HOCON`"

    ```javascript
    s3client {
        someClient {
            bucket = "someBucket" //(1)!
        }
    }
    ```

    1.  Бакет ([bucket](https://aws.amazon.com/s3/faqs/)), в котором будут храниться файлы (`обязательный`, по умолчанию не указано)

=== ":simple-yaml: `YAML`"

    ```yaml
    s3client:
      someClient:
        bucket: "someBucket" #(1)!
    ```

    1.  Бакет ([bucket](https://aws.amazon.com/s3/faqs/)), в котором будут храниться файлы (`обязательный`, по умолчанию не указано)

#### Получение файла { #get-file }

В разделе описана операция получения файла/метаданных с помощью декларативного S3-клиента.
Для указания операции предлагается использовать аннотацию `@S3.Get`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient")
    public interface SomeClient {

        @S3.Get //(1)!
        S3Object operation(String key); //(2)!

        @S3.Get("some-key") //(3)!
        S3Object operation();
    }
    ```

    1. операция получения файла
    2. файл вместе с данными в ответе
    3. ключ файла можно указать в аннотации

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    interface SomeClient {

        @S3.Get //(1)!
        fun operation(key: String): S3Object //(2)!

        @S3.Get("some-key") //(3)!
        fun operation(): S3Object
    }
    ```

    1. операция получения файла
    2. файл вместе с данными в ответе
    3. ключ файла можно указать в аннотации

#### Метаданные { #metadata }

Операция получения файла по ключу может возвращать либо полный файл `S3Object` вместе с данными,
либо облегчённую версию в виде метаданных файла `S3ObjectMeta` без данных;
этот способ значительно быстрее, поскольку не возвращает данные файла.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient")
    public interface SomeClient {

        @S3.Get
        S3ObjectMeta operation(String key); //(1)!
    }
    ```

    1. Получение метаданных файла в ответе

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    interface SomeClient {

        @S3.Get
        fun operation(key: String): S3ObjectMeta //(1)!
    }
    ```

    1. Получение метаданных файла в ответе

#### Шаблон ключа { #key-template }

Ключ также можно задать в виде шаблона и подставлять в него аргументы метода как часть шаблона;
все аргументы метода должны быть частью составного ключа.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient")
    public interface SomeClient {

        @S3.Get("prefix-{key1}-{key2}-suffix") //(1)!
        S3Object operation(String key1, int key2); //(2)!
    }
    ```

    1. Шаблон, используемый для построения ключа: каждый аргумент шаблона подставляется через `toString()`, а аргументы шаблона указываются как имена аргументов метода в `{фигурных скобках}`
    2. Все аргументы метода должны быть частью шаблона ключа

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    interface SomeClient {

        @S3.Get("prefix-{key1}-{key2}-suffix") //(1)!
        fun operation(key1: String, key2: Int): S3Object //(2)!
    }
    ```

    1. Шаблон, используемый для построения ключа: каждый аргумент шаблона подставляется через `toString()`, а аргументы шаблона указываются как имена аргументов метода в `{фигурных скобках}`
    2. Все аргументы метода должны быть частью шаблона ключа

#### Несколько ключей { #multiple-keys }

Также можно получать несколько файлов по ключам — либо как полные объекты с данными (`S3Object`),
либо как облегчённые метаданные без данных объекта (`S3ObjectMeta`).

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient")
    public interface SomeClient {

        @S3.Get //(1)!
        List<S3Object> operation(List<String> keys); //(2)!
    }
    ```

    1. Операция получения по нескольким ключам **не должна** содержать шаблон ключа
    2. Операция должна принимать список ключей и возвращать список `S3Object` или `S3ObjectMeta`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    interface SomeClient {

        @S3.Get //(1)!
        fun operation(keys: List<String>): List<S3Object> //(2)!
    }
    ```

    1. Операция получения по нескольким ключам **не должна** содержать шаблон ключа
    2. Операция должна принимать список ключей и возвращать список `S3Object` или `S3ObjectMeta`

#### Необязательный ответ { #optional-get }

Если отсутствие файла не должно приводить к `S3NotFoundException`, результат `@S3.Get` можно сделать необязательным.
Для стандартных типов `Kora` в `Java` используются `Optional<S3Object>` и `Optional<S3ObjectMeta>`;
модуль `AWS` также поддерживает `Optional<GetObjectResponse>`,
`Optional<ResponseInputStream<GetObjectResponse>>` и `Optional<HeadObjectResponse>`.
В `Kotlin` для тех же случаев используются nullable-типы ответа.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient")
    public interface SomeClient {

        @S3.Get
        Optional<S3Object> object(String key);

        @S3.Get
        Optional<S3ObjectMeta> meta(String key);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    interface SomeClient {

        @S3.Get
        fun object(key: String): S3Object?

        @S3.Get
        fun meta(key: String): S3ObjectMeta?
    }
    ```

### Получение списка файлов { #list-files }

В разделе описана операция получения списка файлов/метаданных с помощью декларативного S3-клиента.
Для указания операции предлагается использовать аннотацию `@S3.List`.

Можно указать [префикс ключа](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-prefixes.html), чтобы выбрать ключи, соответствующие этому префиксу,
а также задать ограничение на выборку файлов с помощью параметра `limit` аннотации `@S3.List`.
Значение `limit` должно находиться в диапазоне `1..1000`, значение по умолчанию — `1000`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient")
    public interface SomeClient {

        @S3.List
        S3ObjectList operation1(String prefix); //(1)!

        @S3.List("some-prefix-") //(2)!
        S3ObjectList operation2();

        @S3.List(limit = 100) //(3)!
        S3ObjectList operation3();
    }
    ```

    1. префикс можно передать как аргумент метода, если он не указан в аннотации
    2. префикс можно указать в аннотации
    3. Можно указать ограничение выборки файлов для операции получения списка через `limit`; допустимый диапазон — `1..1000`, значение по умолчанию — `1000`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    interface SomeClient {

        @S3.List
        fun operation1(prefix: String): S3ObjectList //(1)!

        @S3.List("some-prefix-") //(2)!
        fun operation2(): S3ObjectList

        @S3.List(limit = 100) //(3)!
        fun operation3(): S3ObjectList
    }
    ```

    1. префикс можно передать как аргумент метода, если он не указан в аннотации
    2. префикс можно указать в аннотации
    3. Можно указать ограничение выборки файлов для операции получения списка через `limit`; допустимый диапазон — `1..1000`, значение по умолчанию — `1000`

#### Метаданные { #metadata-2 }

Операция получения списка может возвращать либо полный список файлов `S3ObjectList` вместе с данными,
либо облегчённую версию в виде метаданных файлов `S3ObjectMetaList` без данных;
этот способ значительно быстрее, поскольку не возвращает данные файлов.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient")
    public interface SomeClient {

        @S3.List
        S3ObjectMetaList operation(); //(1)!
    }
    ```

    1. Получение метаданных файлов в ответе

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    interface SomeClient {

        @S3.List
        fun operation(): S3ObjectMetaList //(1)!
    }
    ```

    1. Получение метаданных файлов в ответе

#### Шаблон префикса { #prefix-template }

Префикс также можно задать в виде шаблона и подставлять в него аргументы метода как часть шаблона;
все аргументы метода должны быть частью составного ключа.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient")
    public interface SomeClient {

        @S3.List("prefix-{key1}-{key2}-") //(1)!
        S3ObjectList operation(String key1, int key2);
    }
    ```

    1. Шаблон, используемый для построения префикса: каждый аргумент шаблона подставляется через `toString()`, а аргументы шаблона указываются как имена аргументов метода в `{фигурных скобках}`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    interface SomeClient {

        @S3.List("prefix-{key1}-{key2}-") //(1)!
        fun operation(key1: String, key2: Int): S3ObjectList
    }
    ```

    1. Шаблон, используемый для построения префикса: каждый аргумент шаблона подставляется через `toString()`, а аргументы шаблона указываются как имена аргументов метода в `{фигурных скобках}`

#### Разделитель { #separator }

Можно указать разделитель для [префикса ключа](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-prefixes.html), чтобы отфильтровать результат получения списка:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient")
    public interface SomeClient {

        @S3.List(value = "prefix/foo/bar", delimiter = "/") //(1)!
        S3ObjectList operation();
    }
    ```

    1. Разделитель, используемый для фильтрации списка файлов

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    interface SomeClient {

        @S3.List(value = "prefix/foo/bar", delimiter = "/") //(1)!
        fun operation(): S3ObjectList
    }
    ```

    1. Разделитель, используемый для фильтрации списка файлов

### Добавление файла { #add-file }

В разделе описана операция добавления файла с помощью декларативного S3-клиента.
Для операции предлагается использовать аннотацию `@S3.Put`.

Требуется указать ключ и тело добавляемого файла:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient")
    public interface SomeClient {

        @S3.Put
        void operation1(String key, //(1)!
                        S3Body body); //(2)!

        @S3.Put("some-key") //(3)!
        S3ObjectUpload operation2(S3Body body);
    }
    ```

    1. Ключ файла, по которому он будет добавлен в хранилище
    2. само тело файла, которое будет добавлено в хранилище
    3. ключ также можно указать в аннотации, если он статический

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    interface SomeClient {

        @S3.Put
        fun operation(key: String, body: S3Body)

        @S3.Put("some-key")
        fun operation(body: S3Body): S3ObjectUpload
    }
    ```

    1. Ключ файла, по которому он будет добавлен в хранилище
    2. само тело файла, которое будет добавлено в хранилище
    3. ключ также можно указать в аннотации, если он статический

#### Тело файла { #file-body }

Тело файла (`S3Body`) можно создать из `byte[]`, `ByteBuffer`, `InputStream` или `Flow.Publisher<ByteBuffer>`
с помощью соответствующих статических фабричных методов. Каждый фабричный метод имеет перегрузки, дополнительно принимающие
значения `type` (`Content-Type`) и `encoding` (`Content-Encoding`):

| Фабричный метод                               | Источник                     | Размер     | Описание                                                                                                |
|-----------------------------------------------|------------------------------|------------|--------------------------------------------------------------------------------------------------------|
| `S3Body.ofBytes(byte[])`                      | `byte[]`                     | Известен   | Тело из массива байтов в памяти                                                                         |
| `S3Body.ofBuffer(ByteBuffer)`                 | `ByteBuffer`                 | Известен   | Тело из буфера в памяти (в качестве размера используется `remaining()`)                                 |
| `S3Body.ofInputStream(InputStream, long)`     | `InputStream`                | Известен   | Потоковое тело, точная длина которого передаётся явно через аргумент `size`                             |
| `S3Body.ofInputStreamReadAll(InputStream)`    | `InputStream`                | Известен   | Считывает весь поток в память **немедленно**, затем ведёт себя как массив байтов                        |
| `S3Body.ofInputStreamUnbound(InputStream)`    | `InputStream`                | Неизвестен | Потоковое тело неизвестной длины (`size()` возвращает `-1`)                                             |
| `S3Body.ofPublisher(Flow.Publisher)`          | `Flow.Publisher<ByteBuffer>` | Неизвестен | Реактивное потоковое тело неизвестной длины (`size()` возвращает `-1`)                                  |
| `S3Body.ofPublisher(Flow.Publisher, long)`    | `Flow.Publisher<ByteBuffer>` | Известен   | Реактивное потоковое тело, длина которого передаётся явно через аргумент `size`                         |

Само тело предоставляет следующие методы доступа:

| Метод                                       | Описание                                                                          |
|---------------------------------------------|-----------------------------------------------------------------------------------|
| `byte[] asBytes()`                          | Считывает всё тело в массив байтов (исчерпывает нижележащий поток)                 |
| `InputStream asInputStream()`               | Возвращает тело как блокирующий `InputStream`                                      |
| `Flow.Publisher<ByteBuffer> asPublisher()`  | Возвращает тело как реактивный `Flow.Publisher`                                    |
| `long size()`                               | Длина содержимого в байтах или `-1`, если неизвестна (неограниченный поток / publisher) |
| `String type()`                             | `Content-Type` тела                                                               |
| `String encoding()`                         | `Content-Encoding` тела                                                           |

Если файл очень большой или его длина неизвестна и требуется потоковая передача, рекомендуется создавать тело с помощью
`S3Body.ofPublisher(...)` или `S3Body.ofInputStreamUnbound(...)`.

Если тип файла не указан, будет использован `application/octet-stream`.
Для `@S3.Put` тело также можно передать напрямую как `byte[]` или `ByteBuffer`; в этом случае клиент сам создаёт `S3Body`.
Аннотация `@S3.Put` позволяет указать `type` и `encoding`, которые будут записаны как `Content-Type` и `Content-Encoding`.

`HTTP`-сервер может передавать тело запроса в `S3` потоком, не читая весь файл в память заранее.
Для этого примите тело запроса как `Flow.Publisher<ByteBuffer>` и передайте его в `S3Body.ofPublisher(...)`.
Если размер тела известен, например из заголовка `Content-Length`, лучше передать этот размер в `S3Body`;
если размер неизвестен, используйте перегрузку без размера, и размер будет считаться неизвестным.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController
    public final class UploadController {

        private final S3KoraClient s3;

        public UploadController(S3KoraClient s3) {
            this.s3 = s3;
        }

        @HttpRoute(method = HttpMethod.PUT, path = "/files/{key}")
        public HttpServerResponse upload(@Path String key,
                                         @Header("Content-Type") @Nullable String contentType,
                                         @Header("Content-Length") @Nullable Long contentLength,
                                         Flow.Publisher<ByteBuffer> body) {
            var type = contentType == null ? "application/octet-stream" : contentType;
            var s3Body = contentLength == null
                ? S3Body.ofPublisher(body, type)
                : S3Body.ofPublisher(body, contentLength, type);

            this.s3.put("documents", key, s3Body);
            return HttpServerResponse.of(201);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    @HttpController
    class UploadController(
        private val s3: S3KoraClient
    ) {

        @HttpRoute(method = HttpMethod.PUT, path = "/files/{key}")
        fun upload(
            @Path key: String,
            @Header("Content-Type") contentType: String?,
            @Header("Content-Length") contentLength: Long?,
            body: Flow.Publisher<ByteBuffer>
        ): HttpServerResponse {
            val type = contentType ?: "application/octet-stream"
            val s3Body = if (contentLength == null) {
                S3Body.ofPublisher(body, type)
            } else {
                S3Body.ofPublisher(body, contentLength, type)
            }

            s3.put("documents", key, s3Body)
            return HttpServerResponse.of(201)
        }
    }
    ```

В этом варианте `Kora` получает `Flow.Publisher<ByteBuffer>` из тела `HTTP`-запроса через стандартный
`HttpServerRequestMapper`, а `S3`-клиент читает тот же поток во время загрузки. Обработчику не нужно вызывать
`asBytes()`, `asInputStream().readAllBytes()` или `S3Body.ofInputStreamReadAll(...)`, если цель — не держать весь файл в памяти.

#### Тип и кодировка содержимого { #content-type }

Вместо того чтобы самостоятельно конструировать `S3Body`, можно передать тело напрямую как `byte[]` или `ByteBuffer` и позволить
клиенту обернуть его в `S3Body`. В этом случае для построения тела используются атрибуты `type` (`Content-Type`)
и `encoding` (`Content-Encoding`) аннотации `@S3.Put`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient")
    public interface SomeClient {

        @S3.Put(value = "some-key", type = "image/jpeg", encoding = "gzip") //(1)!
        void operation1(byte[] body); //(2)!

        @S3.Put("some-key")
        void operation2(ByteBuffer body); //(3)!
    }
    ```

    1. `type` сопоставляется с `Content-Type`, а `encoding` — с `Content-Encoding`
    2. Когда тело имеет тип `byte[]` или `ByteBuffer`, клиент сам строит `S3Body`, используя `type`/`encoding` из аннотации
    3. Если не заданы ни `type`, ни `encoding`, в качестве `Content-Type` используется `application/octet-stream`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    interface SomeClient {

        @S3.Put(value = "some-key", type = "image/jpeg", encoding = "gzip") //(1)!
        fun operation1(body: ByteArray) //(2)!

        @S3.Put("some-key")
        fun operation2(body: ByteBuffer) //(3)!
    }
    ```

    1. `type` сопоставляется с `Content-Type`, а `encoding` — с `Content-Encoding`
    2. Когда тело имеет тип `ByteArray` или `ByteBuffer`, клиент сам строит `S3Body`, используя `type`/`encoding` из аннотации
    3. Если не заданы ни `type`, ни `encoding`, в качестве `Content-Type` используется `application/octet-stream`

!!! warning "Тип тела"

    Тело операции `@S3.Put` должно быть `S3Body`, `byte[]` или `ByteBuffer`, иначе возникает ошибка компиляции.
    Атрибуты `type` и `encoding` применяются только к «сырым» телам `byte[]`/`ByteBuffer`; когда передаётся готовый `S3Body`,
    используются его собственные значения `type()`/`encoding()`, а атрибуты аннотации игнорируются.

#### Шаблон ключа { #key-template-2 }

Ключ также можно задать в виде шаблона и подставлять в него аргументы метода как часть шаблона;
все аргументы метода должны быть частью составного ключа.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient")
    public interface SomeClient {

        @S3.Put("prefix-{key1}-{key2}-suffix") //(1)!
        void operation(String key1, int key2, S3Body body); //(2)!
    }
    ```

    1. Шаблон, используемый для построения ключа: каждый аргумент шаблона подставляется через `toString()`, а аргументы шаблона указываются как имена аргументов метода в `{фигурных скобках}`
    2. Все аргументы метода должны быть частью шаблона ключа либо иметь тип `S3Body`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    interface SomeClient {

        @S3.Put("prefix-{key1}-{key2}-suffix") //(1)!
        fun operation(key1: String, key2: Int, body: S3Body) //(2)!
    }
    ```

    1. Шаблон, используемый для построения ключа: каждый аргумент шаблона подставляется через `toString()`, а аргументы шаблона указываются как имена аргументов метода в `{фигурных скобках}`
    2. Все аргументы метода должны быть частью шаблона ключа либо иметь тип `S3Body`

### Удаление файла { #delete-file }

В разделе описана операция удаления файла с помощью декларативного S3-клиента.
Для операции предлагается использовать аннотацию `@S3.Delete`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient")
    public interface SomeClient {

        @S3.Delete //(1)!
        void operation(String key); //(2)!

        @S3.Delete("some-key") //(3)!
        void operation();
    }
    ```

    1. операция удаления файла
    2. Ключ удаляемого файла
    3. Ключ файла можно указать в аннотации

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    interface SomeClient {

        @S3.Delete //(1)!
        fun operation(key: String) //(2)!

        @S3.Delete("some-key") //(3)!
        fun operation()
    }
    ```

    1. операция удаления файла
    2. Ключ удаляемого файла
    3. Ключ файла можно указать в аннотации

#### Шаблон ключа { #key-template-3 }

Ключ также можно задать в виде шаблона и подставлять в него аргументы метода как часть шаблона;
все аргументы метода должны быть частью составного ключа.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient")
    public interface SomeClient {

        @S3.Delete("prefix-{key1}-{key2}-suffix") //(1)!
        void operation(String key1, int key2); //(2)!
    }
    ```

    1. Шаблон, используемый для построения ключа: каждый аргумент шаблона подставляется через `toString()`, а аргументы шаблона указываются как имена аргументов метода в `{фигурных скобках}`
    2. Все аргументы метода должны быть частью шаблона ключа

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    interface SomeClient {

        @S3.Delete("prefix-{key1}-{key2}-suffix") //(1)!
        fun operation(key1: String, key2: Int) //(2)!
    }
    ```

    1. Шаблон, используемый для построения ключа: каждый аргумент шаблона подставляется через `toString()`, а аргументы шаблона указываются как имена аргументов метода в `{фигурных скобках}`
    2. Все аргументы метода должны быть частью шаблона ключа

#### Несколько ключей { #multiple-keys-2 }

Также можно удалять несколько файлов по ключам.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient")
    public interface SomeClient {

        @S3.Delete //(1)!
        void operation(List<String> keys); //(2)!
    }
    ```

    1. Операция удаления по нескольким ключам **не должна** содержать шаблон ключа
    2. Операция должна принимать список ключей и возвращать `void`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    interface SomeClient {

        @S3.Delete //(1)!
        fun operation(keys: List<String>) //(2)!
    }
    ```

    1. Операция удаления по нескольким ключам **не должна** содержать шаблон ключа
    2. Операция должна принимать список ключей и возвращать `void`

### Сигнатуры { #signatures }

Доступные из коробки сигнатуры методов декларативного `S3`-клиента:

===! ":fontawesome-brands-java: `Java`"

    Под `T` подразумевается тип возвращаемого значения.

    - `T myMethod()`
    - `CompletionStage<T> myMethod()` [CompletionStage](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/CompletionStage.html)
    - `CompletableFuture<T> myMethod()` [CompletableFuture](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/CompletableFuture.html)
    - `Mono<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/) (надо подключить [зависимость](https://mvnrepository.com/artifact/io.projectreactor/reactor-core))

=== ":simple-kotlin: `Kotlin`"

    Под `T` подразумевается тип возвращаемого значения, либо `T?`, либо `Unit`.

    - `myMethod(): T`
    - `suspend myMethod(): T` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine) (надо подключить [зависимость](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) как `implementation`)

## Модели { #models }

И декларативные, и императивные клиенты возвращают один и тот же набор типов-моделей (если не используется
[нативный формат ответа](#response-format) модуля `AWS`). Все модели — интерфейсы только для чтения.

### S3Object { #model-s3-object }

Полный объект вместе с его данными, возвращаемый операциями [получения](#get-file) и доступный внутри [S3ObjectList](#model-s3-object-list):

| Метод               | Описание                                                        |
|---------------------|-----------------------------------------------------------------|
| `String key()`      | Ключ объекта                                                     |
| `Instant modified()`| Время последнего изменения                                     |
| `long size()`       | Размер объекта в байтах                                         |
| `S3Body body()`     | [Тело](#file-body) объекта с данными                           |

### S3ObjectMeta { #model-s3-object-meta }

Облегчённые метаданные без данных объекта, возвращаемые операциями [получения](#metadata) метаданных и доступные внутри
[S3ObjectMetaList](#model-s3-object-meta-list). Получение метаданных быстрее, поскольку тело объекта не передаётся:

| Метод                | Описание                        |
|----------------------|---------------------------------|
| `String key()`       | Ключ объекта                    |
| `Instant modified()` | Время последнего изменения      |
| `long size()`        | Размер объекта в байтах         |

### S3ObjectList { #model-s3-object-list }

Список полных объектов, возвращаемый операциями [получения списка](#list-files). Расширяет `S3ObjectMetaList`, поэтому также предоставляет префикс и метаданные:

| Метод                         | Описание                                          |
|-------------------------------|---------------------------------------------------|
| `String prefix()`             | Префикс, использованный для получения списка       |
| `List<S3Object> objects()`    | Объекты, соответствующие префиксу (с данными)      |
| `List<S3ObjectMeta> metas()`  | Метаданные объектов, соответствующих префиксу      |

### S3ObjectMetaList { #model-s3-object-meta-list }

Список метаданных, возвращаемый операциями [получения списка](#metadata-2) метаданных:

| Метод                         | Описание                                        |
|-------------------------------|-------------------------------------------------|
| `String prefix()`             | Префикс, использованный для получения списка     |
| `List<S3ObjectMeta> metas()`  | Метаданные объектов, соответствующих префиксу    |

### S3ObjectUpload { #model-s3-object-upload }

Результат операции [добавления файла](#add-file):

| Метод                 | Описание                                                                    |
|-----------------------|-----------------------------------------------------------------------------|
| `String versionId()`  | Идентификатор версии загруженного объекта (если для бакета включено версионирование) |

## Императивный клиент { #client-imperative }

Для работы с `S3` можно внедрить императивный клиент `Kora`; предоставляются как синхронный, так и асинхронный клиенты:

- `S3KoraClient` - клиент для синхронной работы
- `S3KoraAsyncClient` - клиент для асинхронной работы

Оба клиента работают с явными параметрами `bucket` и `key` и поддерживают получение объектов или метаданных, получение списка объектов по префиксу,
загрузку `S3Body` и удаление одного или нескольких объектов. В отличие от декларативного клиента, они не привязаны к единственному `bucket` из
конфигурации — `bucket` передаётся в каждый метод явно.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeService {

        private final S3KoraClient s3;

        public SomeService(S3KoraClient s3) {
            this.s3 = s3;
        }

        public byte[] download(String bucket, String key) {
            S3Object object = s3.get(bucket, key); //(1)!
            return object.body().asBytes();
        }
    }
    ```

    1. Выбрасывает `S3NotFoundException`, если объект отсутствует

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService(
        private val s3: S3KoraClient
    ) {

        fun download(bucket: String, key: String): ByteArray {
            val obj = s3.get(bucket, key) //(1)!
            return obj.body().asBytes()
        }
    }
    ```

    1. Выбрасывает `S3NotFoundException`, если объект отсутствует

### Синхронный клиент { #client-imperative-sync }

Интерфейс `S3KoraClient` предоставляет следующие операции:

| Метод                                                                                 | Описание                                                          |
|---------------------------------------------------------------------------------------|-------------------------------------------------------------------|
| `S3Object get(bucket, key)`                                                           | Получить один объект с данными                                     |
| `S3ObjectMeta getMeta(bucket, key)`                                                   | Получить метаданные одного объекта                                |
| `List<S3Object> get(bucket, Collection<String> keys)`                                 | Получить несколько объектов с данными                             |
| `List<S3ObjectMeta> getMeta(bucket, Collection<String> keys)`                         | Получить метаданные нескольких объектов                           |
| `S3ObjectList list(bucket[, prefix[, delimiter, limit]])`                             | Получить список объектов по префиксу (с данными)                  |
| `S3ObjectMetaList listMeta(bucket[, prefix[, delimiter, limit]])`                     | Получить список метаданных объектов по префиксу                  |
| `List<S3ObjectList> list(bucket, Collection<String> prefixes[, delimiter, limit])`    | Получить список объектов сразу для нескольких префиксов          |
| `List<S3ObjectMetaList> listMeta(bucket, Collection<String> prefixes[, delimiter, limit])` | Получить список метаданных объектов сразу для нескольких префиксов |
| `S3ObjectUpload put(bucket, key, S3Body body)`                                        | Добавить объект и вернуть результат загрузки                      |
| `void delete(bucket, key)`                                                            | Удалить один объект                                              |
| `void delete(bucket, Collection<String> keys)`                                        | Удалить несколько объектов (при неудаче выбрасывает `S3DeleteException`) |

Перегрузки `list`/`listMeta` без `delimiter`/`limit` по умолчанию используют `null` для `delimiter` и `1000` для `limit`.
Аргумент `limit` должен находиться в диапазоне `1..1000`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    // получить один объект и его метаданные
    S3Object object = s3.get("documents", "report.pdf");
    S3ObjectMeta meta = s3.getMeta("documents", "report.pdf");

    // получить сразу несколько объектов
    List<S3Object> objects = s3.get("documents", List.of("a.pdf", "b.pdf"));

    // получить список по префиксу с разделителем и ограничением
    S3ObjectList list = s3.list("documents", "2024/", "/", 100);
    for (S3Object o : list.objects()) {
        // ...
    }

    // получить список сразу для нескольких префиксов
    List<S3ObjectMetaList> perPrefix = s3.listMeta("documents", List.of("2023/", "2024/"));

    // добавить объект
    S3ObjectUpload upload = s3.put("documents", "report.pdf", S3Body.ofBytes(bytes));
    String versionId = upload.versionId();

    // удалить один объект и пакет объектов
    s3.delete("documents", "report.pdf");
    s3.delete("documents", List.of("a.pdf", "b.pdf"));
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // получить один объект и его метаданные
    val obj = s3.get("documents", "report.pdf")
    val meta = s3.getMeta("documents", "report.pdf")

    // получить сразу несколько объектов
    val objects = s3.get("documents", listOf("a.pdf", "b.pdf"))

    // получить список по префиксу с разделителем и ограничением
    val list = s3.list("documents", "2024/", "/", 100)
    for (o in list.objects()) {
        // ...
    }

    // получить список сразу для нескольких префиксов
    val perPrefix = s3.listMeta("documents", listOf("2023/", "2024/"))

    // добавить объект
    val upload = s3.put("documents", "report.pdf", S3Body.ofBytes(bytes))
    val versionId = upload.versionId()

    // удалить один объект и пакет объектов
    s3.delete("documents", "report.pdf")
    s3.delete("documents", listOf("a.pdf", "b.pdf"))
    ```

### Асинхронный клиент { #client-imperative-async }

Интерфейс `S3KoraAsyncClient` повторяет `S3KoraClient` метод в метод, но каждая операция возвращает
[CompletionStage](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/CompletionStage.html)
(`CompletionStage<Void>` для операций удаления):

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeService {

        private final S3KoraAsyncClient s3;

        public SomeService(S3KoraAsyncClient s3) {
            this.s3 = s3;
        }

        public CompletionStage<byte[]> download(String bucket, String key) {
            return s3.get(bucket, key)
                .thenApply(object -> object.body().asBytes());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService(
        private val s3: S3KoraAsyncClient
    ) {

        fun download(bucket: String, key: String): CompletionStage<ByteArray> {
            return s3.get(bucket, key)
                .thenApply { it.body().asBytes() }
        }
    }
    ```

## Нативные клиенты { #native-clients }

Помимо декларативных и императивных клиентов `Kora`, для внедрения также доступны нижележащие нативные клиенты `SDK`.
Они полезны для расширенных операций, не покрываемых декларативным/императивным API (например, управление бакетами, копирование
объектов, предподписанные (presigned) URL и так далее).

[Модуль AWS](#aws) предоставляет:

- `S3Client` — синхронный клиент `AWS`
- `S3AsyncClient` — асинхронный клиент `AWS`
- `S3AsyncClient` с `@Tag(MultipartUpload.class)` — асинхронный клиент `AWS`, предварительно настроенный для [многочастной загрузки](https://sdk.amazonaws.com/java/api/latest/software/amazon/awssdk/services/s3/internal/multipart/MultipartS3AsyncClient.html) в соответствии с `upload.partSize` и `upload.bufferSize`

[Модуль Minio](#minio) предоставляет:

- `MinioClient` — синхронный клиент `Minio`
- `MinioAsyncClient` — асинхронный клиент `Minio`

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class BucketService {

        private final S3Client s3Client; //(1)!
        private final S3AsyncClient multipartClient;

        public BucketService(S3Client s3Client,
                             @Tag(MultipartUpload.class) S3AsyncClient multipartClient) { //(2)!
            this.s3Client = s3Client;
            this.multipartClient = multipartClient;
        }

        public void ensureBucket(String bucket) {
            s3Client.createBucket(b -> b.bucket(bucket));
        }
    }
    ```

    1. Нативный `S3Client` из `AWS`, внедряемый напрямую
    2. Асинхронный клиент с тегом `@Tag(MultipartUpload.class)` для многочастной загрузки

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class BucketService(
        private val s3Client: S3Client, //(1)!
        @Tag(MultipartUpload::class) private val multipartClient: S3AsyncClient //(2)!
    ) {

        fun ensureBucket(bucket: String) {
            s3Client.createBucket { it.bucket(bucket) }
        }
    }
    ```

    1. Нативный `S3Client` из `AWS`, внедряемый напрямую
    2. Асинхронный клиент с тегом `@Tag(MultipartUpload::class)` для многочастной загрузки

## Исключения { #exceptions }

Если операция клиента завершается неудачей, выбрасывается одно из исключений `S3`. Все они наследуются от базового `S3Exception`,
который, в свою очередь, расширяет `RuntimeException`, поэтому их обработка необязательна и не проверяется компилятором.

**Иерархия исключений:**

```
RuntimeException
└── S3Exception
    ├── S3NotFoundException
    └── S3DeleteException
```

Базовое исключение `S3Exception` предоставляет код ошибки и сообщение, сообщённые хранилищем:

| Метод                       | Описание                                             |
|-----------------------------|------------------------------------------------------|
| `String getErrorCode()`     | Код ошибки хранилища (например, `NoSuchKey`)         |
| `String getErrorMessage()`  | Сообщение об ошибке хранилища                        |

**Пример обработки:**

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeService {

        private final S3KoraClient s3;

        public SomeService(S3KoraClient s3) {
            this.s3 = s3;
        }

        public void call(String bucket) {
            try {
                s3.delete(bucket, List.of("a.pdf", "b.pdf"));
            } catch (S3NotFoundException e) {
                // Объект или бакет отсутствует: getErrorCode() возвращает NoSuchKey или NoSuchBucket
            } catch (S3DeleteException e) {
                // Один или несколько объектов не были удалены
                for (S3DeleteException.Error error : e.getErrors()) {
                    // error.key(), error.bucket(), error.code(), error.message()
                }
            } catch (S3Exception e) {
                // Любая другая ошибка хранилища: getErrorCode(), getErrorMessage()
            }
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService(
        private val s3: S3KoraClient
    ) {

        fun call(bucket: String) {
            try {
                s3.delete(bucket, listOf("a.pdf", "b.pdf"))
            } catch (e: S3NotFoundException) {
                // Объект или бакет отсутствует: errorCode равен NoSuchKey или NoSuchBucket
            } catch (e: S3DeleteException) {
                // Один или несколько объектов не были удалены
                for (error in e.errors) {
                    // error.key(), error.bucket(), error.code(), error.message()
                }
            } catch (e: S3Exception) {
                // Любая другая ошибка хранилища: errorCode, errorMessage
            }
        }
    }
    ```

### S3NotFoundException { #not-found-exception }

Выбрасывается, когда запрошенный объект или бакет не существует.

**Причины:**

- Ключ объекта не существует (`getErrorCode()` возвращает `NoSuchKey`)
- Бакет не существует (`getErrorCode()` возвращает `NoSuchBucket`)

**Рекомендации:**

- Сделайте результат `@S3.Get` [необязательным](#optional-get) (`Optional`/nullable), если отсутствие объекта — нормальный исход
- Проверьте `bucket` из конфигурации и запрошенный `key`

### S3DeleteException { #delete-exception }

Выбрасывается пакетными операциями `delete(bucket, keys)`, когда один или несколько объектов не удалось удалить.
Предоставляет список отдельных сбоев:

| Метод                     | Описание                                                       |
|---------------------------|----------------------------------------------------------------|
| `List<Error> getErrors()` | Сбои по каждому объекту, каждый с `key()`, `bucket()`, `code()`, `message()` |

**Рекомендации:**

- Изучите `getErrors()`, чтобы определить, какие объекты не удалось обработать и почему
- Повторите неудавшиеся ключи отдельно, если сбой временный

### S3Exception { #base-exception }

Базовое исключение, выбрасываемое при любой другой ошибке хранилища или клиента, не связанной с отсутствием объекта или сбоем пакетного удаления.

**Рекомендации:**

- Логируйте `getErrorCode()` и `getErrorMessage()` для диагностики
- Включите [логирование](#configuration) клиента на уровне `DEBUG`, чтобы изучить нижележащий запрос/ответ

## Тестирование { #testing }

Декларативные и императивные `S3`-клиенты можно тестировать с помощью [@KoraAppTest](junit5.md) вместе с реальным
`S3`-совместимым хранилищем, запущенным в контейнере [Testcontainers](https://java.testcontainers.org/) (например, `Minio`).
Параметры подключения к хранилищу передаются в конфигурацию приложения через системные свойства:

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
        void putAndGet() {
            var value = "value".getBytes(StandardCharsets.UTF_8);
            client.putObject("k1", S3Body.ofBytes(value));

            var found = client.getObject("k1");
            assertArrayEquals(value, found.body().asBytes());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @TestcontainersMinio(
        mode = ContainerMode.PER_RUN,
        bucket = Bucket(value = [BUCKET], create = Bucket.Mode.PER_METHOD, drop = Bucket.Mode.PER_METHOD))
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
            val value = "value".toByteArray()
            client.putObject("k1", S3Body.ofBytes(value))

            val found = client.getObject("k1")
            assertArrayEquals(value, found.body().asBytes())
        }

        companion object {
            const val BUCKET = "simple"
        }
    }
    ```
