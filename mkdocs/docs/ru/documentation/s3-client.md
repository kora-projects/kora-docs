---
description: "Explains Kora S3 clients for AWS and Minio, declarative and imperative clients, file operations, metadata, key templates, and exception handling. Use when working with @S3.Client, @S3.Get, @S3.List, @S3.Put, @S3.Delete, S3ClientModule, AwsS3Client, MinioS3Client."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora S3 clients for AWS and Minio, declarative and imperative clients, file operations, metadata, key templates, and exception handling; key triggers include @S3.Client, @S3.Get, @S3.List, @S3.Put, @S3.Delete, S3ClientModule, AwsS3Client, MinioS3Client."
---

??? warning "Экспериментальный модуль"

    **Экспериментальный** модуль является полностью рабочим и протестированным, но требует дополнительной апробации и аналитики по использованию,
    поэтому API может потенциально претерпеть незначительные изменения перед полной готовностью.

Модуль предоставляет слой абстракции для работы с [S3-совместимым объектным хранилищем](https://aws.amazon.com/ru/s3/faqs/):
можно создавать декларативные `S3`-клиенты с помощью аннотаций или внедрять готовые императивные клиенты.
Декларативный клиент удобен для типовых операций с объектами и ключами, а императивный клиент подходит, когда нужно управлять
операциями напрямую в коде.

Если нужен пошаговый разбор перед справочным описанием, смотрите [S3](../guides/s3.md).

## AWS { #aws }

Реализация `S3`-клиента, основанная на библиотеке [AWS](https://github.com/aws/aws-sdk-java-v2).

Для работы и внедрения доступны компоненты:

- Императивные [Kora S3 клиенты](#client-imperative)
- `S3Client` синхронный AWS S3 клиент
- `S3AsyncClient` асинхронный AWS S3 клиент
- `S3AsyncClient` с тегом `@Tag(MultipartUpload.class)` асинхронный AWS S3 клиент для пакетной загрузки

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

Требуется подключить любой модуль [HTTP-клиента](http-client.md).

### Конфигурация { #configuration }

Пример полной конфигурации, описанной в классе `AwsS3ClientConfig` и `S3Config` (указаны примеры значений или значения по умолчанию):

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

    1.  Тип доступа к объектам, может иметь значения `PATH` или `VIRTUAL_HOSTED` (по умолчанию: `PATH`)
    2.  Максимальное время выполнения операции (по умолчанию: `45s`)
    3.  Проверять ли контрольную сумму [MD5 файлов перед загрузкой и при получении](https://sdk.amazonaws.com/java/api/latest/software/amazon/awssdk/services/s3/S3Configuration.Builder.html#checksumValidationEnabled(java.lang.Boolean)) из `AWS` (по умолчанию: `false`)
    4.  Кодировать ли данные кусками при подписании файла во время загрузки в `AWS` (по умолчанию: `true`)
    5.  Максимальный размер буфера при загрузке файлов (по умолчанию: `32MiB`)
    6.  Максимальный размер части файла при единовременной загрузке файла (по умолчанию: `8MiB`)
    7.  `URL` `S3`-хранилища (`обязательная`, по умолчанию не указано)
    8.  Ключ доступа к `S3` (`обязательная`, по умолчанию не указано)
    9.  Секрет доступа к `S3` (`обязательная`, по умолчанию не указано)
    10. Регион `S3`-хранилища (по умолчанию: `aws-global`)
    11. Включает логирование модуля (по умолчанию: `false`)
    12. Включает метрики модуля (по умолчанию: `true`)
    13. Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    14. Настройка тегов для метрик (по умолчанию: `{}`)
    15. Включает трассировку модуля (по умолчанию: `true`)
    16. Настройка атрибутов для трассировки (по умолчанию: `{}`)

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

    1.  Тип доступа к объектам, может иметь значения `PATH` или `VIRTUAL_HOSTED` (по умолчанию: `PATH`)
    2.  Максимальное время выполнения операции (по умолчанию: `45s`)
    3.  Проверять ли контрольную сумму [MD5 файлов перед загрузкой и при получении](https://sdk.amazonaws.com/java/api/latest/software/amazon/awssdk/services/s3/S3Configuration.Builder.html#checksumValidationEnabled(java.lang.Boolean)) из `AWS` (по умолчанию: `false`)
    4.  Кодировать ли данные кусками при подписании файла во время загрузки в `AWS` (по умолчанию: `true`)
    5.  Максимальный размер буфера при загрузке файлов (по умолчанию: `32MiB`)
    6.  Максимальный размер части файла при единовременной загрузке файла (по умолчанию: `8MiB`)
    7.  `URL` `S3`-хранилища (`обязательная`, по умолчанию не указано)
    8.  Ключ доступа к `S3` (`обязательная`, по умолчанию не указано)
    9.  Секрет доступа к `S3` (`обязательная`, по умолчанию не указано)
    10. Регион `S3`-хранилища (по умолчанию: `aws-global`)
    11. Включает логирование модуля (по умолчанию: `false`)
    12. Включает метрики модуля (по умолчанию: `true`)
    13. Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    14. Настройка тегов для метрик (по умолчанию: `{}`)
    15. Включает трассировку модуля (по умолчанию: `true`)
    16. Настройка атрибутов для трассировки (по умолчанию: `{}`)

Предоставляемые метрики модуля описаны в разделе [Справочник метрик](metrics.md#s3-client).

### Формат ответа { #response-format }

В случае использования `AWS` модуля есть возможность получать специальные форматы ответа, специфичные только для `AWS` библиотеки:

| Операция                          | Формат ответа                                                                                                                                                                                                                                                                 |
|-----------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| [Получение файла](#get-file)            | [GetObjectResponse](https://sdk.amazonaws.com/java/api/latest/software/amazon/awssdk/services/s3/model/GetObjectResponse.html) / [ResponseInputStream<GetObjectResponse>](https://sdk.amazonaws.com/java/api/latest/software/amazon/awssdk/core/ResponseInputStream.html)     |
| [Получение метаданных файла](#metadata) | [HeadObjectResponse](https://sdk.amazonaws.com/java/api/latest/software/amazon/awssdk/services/s3/model/HeadObjectResponse.html)                                                                                                                                              |
| [Перечисление файлов](#list-files)       | [ListObjectsV2Response](https://sdk.amazonaws.com/java/api/latest/software/amazon/awssdk/services/s3/model/ListObjectsV2Response.html)                                                                                                                                        |
| [Добавление файла](#add-file)          | [PutObjectResponse](https://sdk.amazonaws.com/java/api/latest/software/amazon/awssdk/services/s3/model/PutObjectResponse.html)                                                                                                                                                |
| [Удаление файла](#delete-file)            | [DeleteObjectResponse](https://sdk.amazonaws.com/java/api/latest/software/amazon/awssdk/services/s3/model/DeleteObjectResponse.html) / [DeleteObjectsResponse](https://sdk.amazonaws.com/java/api/latest/software/amazon/awssdk/services/s3/model/DeleteObjectsResponse.html) |

Для операций `@S3.Get`, которые получают файл или метаданные, можно описать отсутствие объекта в типе ответа.
В `Java` поддерживаются `Optional<S3Object>`, `Optional<S3ObjectMeta>`, `Optional<GetObjectResponse>`,
`Optional<ResponseInputStream<GetObjectResponse>>` и `Optional<HeadObjectResponse>`.
В `Kotlin` для этого используются типы с возможностью значения `null`: `S3Object?`, `S3ObjectMeta?`, `GetObjectResponse?`,
`ResponseInputStream<GetObjectResponse>?` и `HeadObjectResponse?`.

## Minio { #minio }

Реализация `S3`-клиента, основанная на библиотеке [Minio](https://github.com/minio/minio-java).
Учитывайте, что реализация использует [OkHttp](https://github.com/square/okhttp), написанный на `Kotlin`, и его зависимости.

Для работы и внедрения доступны компоненты:

- Императивные [Kora S3 клиенты](#client-imperative)
- `MinioClient` синхронный Minio S3 клиент
- `MinioAsyncClient` асинхронный Minio S3 клиент

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

Можно подключить [OkHttp модуль](http-client.md#okhttp) либо будет создан стандартный HTTP-клиент.

### Конфигурация { #configuration-2 }

Пример полной конфигурации, описанной в классе `MinioS3ClientConfig` и `S3Config` (указаны примеры значений или значения по умолчанию):

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

    1.  Тип доступа к объектам, может иметь значения `PATH` или `VIRTUAL_HOSTED` (по умолчанию: `PATH`)
    2.  Максимальное время выполнения операции (по умолчанию: `45s`)
    3.  Максимальный размер части файла при единовременной загрузке файла (по умолчанию: `8MiB`)
    4.  `URL` `S3`-хранилища (`обязательная`, по умолчанию не указано)
    5.  Ключ доступа к `S3` (`обязательная`, по умолчанию не указано)
    6.  Секрет доступа к `S3` (`обязательная`, по умолчанию не указано)
    7.  Регион `S3`-хранилища (по умолчанию: `aws-global`)
    8.  Включает логирование модуля (по умолчанию: `false`)
    9.  Включает метрики модуля (по умолчанию: `true`)
    10. Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    11. Настройка тегов для метрик (по умолчанию: `{}`)
    12. Включает трассировку модуля (по умолчанию: `true`)
    13. Настройка атрибутов для трассировки (по умолчанию: `{}`)

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

    1.  Тип доступа к объектам, может иметь значения `PATH` или `VIRTUAL_HOSTED` (по умолчанию: `PATH`)
    2.  Максимальное время выполнения операции (по умолчанию: `45s`)
    3.  Максимальный размер части файла при единовременной загрузке файла (по умолчанию: `8MiB`)
    4.  `URL` `S3`-хранилища (`обязательная`, по умолчанию не указано)
    5.  Ключ доступа к `S3` (`обязательная`, по умолчанию не указано)
    6.  Секрет доступа к `S3` (`обязательная`, по умолчанию не указано)
    7.  Регион `S3`-хранилища (по умолчанию: `aws-global`)
    8.  Включает логирование модуля (по умолчанию: `false`)
    9.  Включает метрики модуля (по умолчанию: `true`)
    10. Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    11. Настройка тегов для метрик (по умолчанию: `{}`)
    12. Включает трассировку модуля (по умолчанию: `true`)
    13. Настройка атрибутов для трассировки (по умолчанию: `{}`)

## Клиент декларативный { #client-declarative }

Предлагается использовать специальные аннотации для создания декларативного клиента:

* `@S3.Client` — указывает что интерфейс является декларативным S3-клиентом
* `@S3.Get` — указывает, что метод выполняет операцию [получения файла или метаданных](#get-file)
* `@S3.List` — указывает, что метод выполняет операцию [получения списка файлов или метаданных](#list-files)
* `@S3.Put` — указывает, что метод выполняет операцию [добавления файла](#add-file)
* `@S3.Delete` — указывает, что метод выполняет операцию [удаления файла](#delete-file)

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

    1. Путь до конфигурации конкретно этого клиента

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient") //(1)!
    interface SomeClient {

        @S3.Get
        fun operation(key: String): S3Object
    }
    ```

    1. Путь до конфигурации конкретно этого клиента

`@S3.Client` без аргументов эквивалентна `@S3.Client("")`: значение `value` у аннотации пустое,
и `S3ClientConfig` будет прочитан по пустому пути через `Config.get("")`.
На практике обычно указывают явный путь, например `@S3.Client("s3client.someClient")`, чтобы конфигурация `bucket` была отделена от настроек других клиентов.

Пример конфигурации в случае пути `s3client.someClient` описанной в классе `S3ClientConfig`:

===! ":material-code-json: `HOCON`"

    ```javascript
    s3client {
        someClient {
            bucket = "someBucket" //(1)!
        }
    }
    ```

    1.  Корзина ([bucket](https://aws.amazon.com/ru/s3/faqs/)), где будут храниться файлы (`обязательная`, по умолчанию не указано)

=== ":simple-yaml: `YAML`"

    ```yaml
    s3client:
      someClient:
        bucket: "someBucket" #(1)!
    ```

    1.  Корзина ([bucket](https://aws.amazon.com/ru/s3/faqs/)), где будут храниться файлы (`обязательная`, по умолчанию не указано)

### Получение файла { #get-file }

Секция описывает операцию получения файла/метаданных с помощью декларативного S3-клиента.
Предлагается использовать аннотацию `@S3.Get` для указания операции.

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

    1. Операция получения файла
    2. Возвращает файл вместе с данными
    3. Ключ файла можно указать в аннотации

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

    1. Операция получения файла
    2. Возвращает файл вместе с данными
    3. Ключ файла можно указать в аннотации

#### Метаданные { #metadata }

Операция получения файла по ключу может возвращать как полный файл вместе с данными `S3Object`,
так и облегченный вариант в виде метаданных файла без данных `S3ObjectMeta`,
такой метод выполняется значительно быстрее, так как не возвращает данные файла.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient")
    public interface SomeClient {

        @S3.Get
        S3ObjectMeta operation(String key); //(1)!
    }
    ```

    1. Получение в ответ метаданных файла

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    interface SomeClient {

        @S3.Get
        fun operation(key: String): S3ObjectMeta //(1)!
    }
    ```

    1. Получение в ответ метаданных файла

#### Шаблон ключа { #key-template }

Ключ можно указывать также как шаблон и подставлять туда аргументы метода как части шаблона,
все аргументы метода должны быть частью составного ключа.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient")
    public interface SomeClient {

        @S3.Get("prefix-{key1}-{key2}-suffix") //(1)!
        S3Object operation(String key1, int key2); //(2)!
    }
    ```

    1. Шаблон, по которому будет собран ключ: каждый аргумент шаблона будет подставлен через `toString()`, а аргументы в шаблоне указываются как имена аргументов метода в `{фигурных скобках}`
    2. Все аргументы метода должны быть частью шаблона ключа

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    interface SomeClient {

        @S3.Get("prefix-{key1}-{key2}-suffix") //(1)!
        fun operation(key1: String, key2: Int): S3Object //(2)!
    }
    ```

    1. Шаблон, по которому будет собран ключ: каждый аргумент шаблона будет подставлен через `toString()`, а аргументы в шаблоне указываются как имена аргументов метода в `{фигурных скобках}`
    2. Все аргументы метода должны быть частью шаблона ключа

#### Множество ключей { #multiple-keys }

Можно также получать сразу множество файлов по ключам как полный файл вместе с данными `S3Object`,
так и облегченный вариант в виде множества метаданных файлов без данных `S3ObjectMeta`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient")
    public interface SomeClient {

        @S3.Get //(1)!
        List<S3Object> operation(List<String> keys); //(2)!
    }
    ```

    1. Операция получения файлов для множества ключей **не должна** содержать шаблон ключа
    2. Операция должна принимать список ключей и отдавать список `S3Object` либо `S3ObjectMeta`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    interface SomeClient {

        @S3.Get //(1)!
        fun operation(keys: List<String>): List<S3Object> //(2)!
    }
    ```

    1. Операция получения файлов для множества ключей **не должна** содержать шаблон ключа
    2. Операция должна принимать список ключей и отдавать список `S3Object` либо `S3ObjectMeta`

#### Необязательный ответ { #optional-get }

Если отсутствие файла не должно приводить к исключению `S3NotFoundException`, то результат `@S3.Get` можно сделать необязательным.
Для обычных `Kora` типов в `Java` используются `Optional<S3Object>` и `Optional<S3ObjectMeta>`,
а для `AWS` модуля также поддерживаются `Optional<GetObjectResponse>`,
`Optional<ResponseInputStream<GetObjectResponse>>` и `Optional<HeadObjectResponse>`.
В `Kotlin` для тех же типов используются ответы с возможностью значения `null`.

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

### Перечисление файлов { #list-files }

Секция описывает операцию получения списка файлов/метаданных с помощью декларативного S3-клиента.
Предлагается использовать аннотацию `@S3.List` для указания операции.

Можно указывать [префикс ключа](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-prefixes.html), чтобы делать выборку по нужным ключам подходящим под префикс,
также можно указывать ограничение по выборке файлов через параметр `limit` у `@S3.List`.
Значение `limit` должно быть в диапазоне `1..1000`, по умолчанию используется `1000`.

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

    1. Префикс можно передать как аргумент метода, если он не указан в аннотации
    2. Префикс можно указать в аннотации
    3. Можно указывать ограничение по выборке файлов для операции перечисления через `limit`; допустимый диапазон `1..1000`, по умолчанию используется `1000`

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

    1. Префикс можно передать как аргумент метода, если он не указан в аннотации
    2. Префикс можно указать в аннотации
    3. Можно указывать ограничение по выборке файлов для операции перечисления через `limit`; допустимый диапазон `1..1000`, по умолчанию используется `1000`

#### Метаданные { #metadata-2 }

Операция получения файла по ключу может возвращать как полный файл вместе с данными `S3ObjectList`,
так и облегченный вариант в виде метаданных файла без данных `S3ObjectMetaList`,
такой метод выполняется значительно быстрее, так как не возвращает данные файлов.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient")
    public interface SomeClient {

        @S3.List
        S3ObjectMetaList operation(); //(1)!
    }
    ```

    1. Получение в ответ метаданных файлов

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    interface SomeClient {

        @S3.List
        fun operation(): S3ObjectMetaList //(1)!
    }
    ```

    1. Получение в ответ метаданных файлов

#### Шаблон префикса { #prefix-template }

Префикс можно указывать также как шаблон и подставлять туда аргументы метода как части шаблона,
все аргументы метода должны быть частью составного ключа.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient")
    public interface SomeClient {

        @S3.List("prefix-{key1}-{key2}-") //(1)!
        S3ObjectList operation(String key1, int key2);
    }
    ```

    1. Шаблон, по которому будет собран префикс: каждый аргумент шаблона будет подставлен через `toString()`, а аргументы в шаблоне указываются как имена аргументов метода в `{фигурных скобках}`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    interface SomeClient {

        @S3.List("prefix-{key1}-{key2}-") //(1)!
        fun operation(key1: String, key2: Int): S3ObjectList
    }
    ```

    1. Шаблон, по которому будет собран префикс: каждый аргумент шаблона будет подставлен через `toString()`, а аргументы в шаблоне указываются как имена аргументов метода в `{фигурных скобках}`

#### Разделитель { #separator }

Можно указывать разделитель для [префикса ключа](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-prefixes.html), исключать нужные файлы из выборки:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient")
    public interface SomeClient {

        @S3.List(value = "prefix/foo/bar", delimiter = "/") //(1)!
        S3ObjectList operation();
    }
    ```

    1. Разделитель, по которому будет фильтроваться перечисление файлов

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    interface SomeClient {

        @S3.List(value = "prefix/foo/bar", delimiter = "/") //(1)!
        fun operation(): S3ObjectList
    }
    ```

    1. Разделитель, по которому будет фильтроваться перечисление файлов

### Добавление файла { #add-file }

Секция описывает операцию добавления файла с помощью декларативного S3-клиента.
Предлагается использовать аннотацию `@S3.Put` для операции.

Требуется указать ключ и тело файла для добавления:

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

    1. Ключ файла по которому он будет добавлен в хранилище
    2. Само тело файла которое будет добавлено в хранилище
    3. Ключ также можно указать в аннотации если он статичен

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

    1. Ключ файла по которому он будет добавлен в хранилище
    2. Само тело файла которое будет добавлено в хранилище
    3. Ключ также можно указать в аннотации если он статичен

#### Тело файла { #file-body }

Тело файла (`S3Body`) может быть создано из `byte[]`, `ByteBuffer`, `InputStream` или `Flow.Publisher<ByteBuffer>`
через соответствующие статические методы-фабрики: `ofBytes(...)`, `ofBuffer(...)`, `ofInputStream(...)`,
`ofInputStreamReadAll(...)`, `ofInputStreamUnbound(...)` и `ofPublisher(...)`.

Если файл очень большой либо неизвестна его длина и требуется потоковая загрузка, рекомендуется создавать тело с помощью
`S3Body.ofPublisher(...)` либо `S3Body.ofInputStreamUnbound(...)`.

Если тип файла не указан, будет использован `application/octet-stream`.
Для `@S3.Put` тело также можно передать напрямую как `byte[]` или `ByteBuffer`; в таком случае клиент сам создаст `S3Body`.
Аннотация `@S3.Put` позволяет указать `type` и `encoding`, которые будут записаны как `Content-Type` и `Content-Encoding`.

`HTTP`-сервер может передавать тело запроса в `S3` потоково, без предварительного чтения всего файла в память.
Для этого тело запроса принимается как `Flow.Publisher<ByteBuffer>` и передается в `S3Body.ofPublisher(...)`.
Если известен размер тела, например из заголовка `Content-Length`, лучше передать его в `S3Body`; если размер неизвестен,
можно использовать перегрузку без размера, тогда размер будет считаться неизвестным.

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

В таком варианте `Kora` берет `Flow.Publisher<ByteBuffer>` из тела `HTTP`-запроса через стандартный `HttpServerRequestMapper`,
а `S3`-клиент читает тот же поток во время загрузки. В обработчике не нужно вызывать `asBytes()`,
`asInputStream().readAllBytes()` или `S3Body.ofInputStreamReadAll(...)`, если цель — не держать весь файл в памяти.

#### Шаблон ключа { #key-template-2 }

Ключ можно указывать также как шаблон и подставлять туда аргументы метода как части шаблона,
все аргументы метода должны быть частью составного ключа.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient")
    public interface SomeClient {

        @S3.Put("prefix-{key1}-{key2}-suffix") //(1)!
        void operation(String key1, int key2, S3Body body); //(2)!
    }
    ```

    1. Шаблон, по которому будет собран ключ: каждый аргумент шаблона будет подставлен через `toString()`, а аргументы в шаблоне указываются как имена аргументов метода в `{фигурных скобках}`
    2. Все аргументы метода должны быть частью шаблона ключа либо `S3Body`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    interface SomeClient {

        @S3.Put("prefix-{key1}-{key2}-suffix") //(1)!
        fun operation(key1: String, key2: Int, body: S3Body) //(2)!
    }
    ```

    1. Шаблон, по которому будет собран ключ: каждый аргумент шаблона будет подставлен через `toString()`, а аргументы в шаблоне указываются как имена аргументов метода в `{фигурных скобках}`
    2. Все аргументы метода должны быть частью шаблона ключа либо `S3Body`

### Удаление файла { #delete-file }

Секция описывает операцию удаления файла с помощью декларативного `S3`-клиента.
Предлагается использовать аннотацию `@S3.Delete` для операции.

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

    1. Операция удаления файла
    2. Ключ файла, который будет удален
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

    1. Операция удаления файла
    2. Ключ файла, который будет удален
    3. Ключ файла можно указать в аннотации

#### Шаблон ключа { #key-template-3 }

Ключ можно указывать также как шаблон и подставлять туда аргументы метода как части шаблона,
все аргументы метода должны быть частью составного ключа.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient")
    public interface SomeClient {

        @S3.Delete("prefix-{key1}-{key2}-suffix") //(1)!
        void operation(String key1, int key2); //(2)!
    }
    ```

    1. Шаблон, по которому будет собран ключ: каждый аргумент шаблона будет подставлен через `toString()`, а аргументы в шаблоне указываются как имена аргументов метода в `{фигурных скобках}`
    2. Все аргументы метода должны быть частью шаблона ключа

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    interface SomeClient {

        @S3.Delete("prefix-{key1}-{key2}-suffix") //(1)!
        fun operation(key1: String, key2: Int) //(2)!
    }
    ```

    1. Шаблон, по которому будет собран ключ: каждый аргумент шаблона будет подставлен через `toString()`, а аргументы в шаблоне указываются как имена аргументов метода в `{фигурных скобках}`
    2. Все аргументы метода должны быть частью шаблона ключа

#### Множество ключей { #multiple-keys-2 }

Можно также удалить сразу множество файлов по ключам.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient")
    public interface SomeClient {

        @S3.Delete //(1)!
        void operation(List<String> keys); //(2)!
    }
    ```

    1. Операция удаления файлов для множества ключей **не должна** содержать шаблон ключа
    2. Операция должна принимать список ключей и отдавать `void`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    interface SomeClient {

        @S3.Delete //(1)!
        fun operation(keys: List<String>) //(2)!
    }
    ```

    1. Операция удаления файлов для множества ключей **не должна** содержать шаблон ключа
    2. Операция должна принимать список ключей и отдавать `void`

### Сигнатуры { #signatures }

Доступные сигнатуры для методов декларативного `S3`-клиента из коробки:

===! ":fontawesome-brands-java: `Java`"

    Под `T` подразумевается тип возвращаемого значения, либо `Void`.

    - `T myMethod()`
    - `CompletionStage<T> myMethod()` [CompletionStage](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/CompletionStage.html)
    - `CompletableFuture<T> myMethod()` [CompletableFuture](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/CompletableFuture.html)
    - `Mono<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/) (надо подключить [зависимость](https://mvnrepository.com/artifact/io.projectreactor/reactor-core))

=== ":simple-kotlin: `Kotlin`"

    Под `T` подразумевается тип возвращаемого значения, либо `Unit`.

    - `myMethod(): T`
    - `suspend myMethod(): T` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine) (надо подключить [зависимость](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) как `implementation`)

## Клиент императивный { #client-imperative }

Можно внедрить императивный `Kora`-клиент для работы с `S3`; предоставляется клиент как для синхронной, так и для асинхронной работы:

- `S3KoraClient` - клиент для синхронной работы
- `S3KoraAsyncClient` - клиент для асинхронной работы

Оба клиента работают с явными параметрами `bucket` и `key`, поддерживают получение объекта или метаданных, перечисление
объектов по префиксу, загрузку `S3Body` и удаление одного или нескольких объектов.

## Ошибки { #exceptions }

В случае ошибки работы клиента будут брошены специальные ошибки:

- `S3NotFoundException` - если файл или корзина не найдены
- `S3DeleteException` - в случае ошибки удаления одного или нескольких файлов
- `S3Exception` - в любом другом случае
