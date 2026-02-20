??? warning "Экспериментальный модуль"

    **Эксперементальный** модуль является полностью рабочим и протестированным, но требует дополнительной апробации и аналитики по использованию, 
    по этой причине API может потенциально притерпеть незначительные изменения перед полной готовностью.

Модуль предоставляет тонкий слой абстракции для создания S3-клиентов
с помощью аннотаций в декларативном стиле, либо использование клиентов в императивном стиле для работы с [хранилищем S3](https://aws.amazon.com/ru/s3/faqs/).

## AWS

Реализация S3-клиента основанная на библиотеке [AWS](https://github.com/aws/aws-sdk-java-v2).

Для работы и внедрения доступны компоненты:

- Императивные [Kora S3 клиенты](#_23)
- `S3Client` синхронный AWS S3 клиент
- `S3AsyncClient` асинхронный AWS S3 клиент
- `S3AsyncClient` с тегом `@Tag(MultipartUpload.class)` асинхронный AWS S3 клиент для пакетной загрузки

### Подключение

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#_4) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora.experimental:s3-client-aws"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends AwsS3ClientModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#_4) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora.experimental:s3-client-aws")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : AwsS3ClientModule
    ```

Требуется подключить любой модуль [HTTP-клиента](http-client.md).

### Конфигурация

Пример полной конфигурации, описанной в классе `AwsS3ClientConfig` и `S3Config` (указаны примеры значений или значения по умолчанию):

===! ":material-code-json: `Hocon`"

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
            }
            tracing {
                enabled = true //(14)!
            }
        }
    }
    ```

    1.  Какой тип доступа к [файлам использовать](https://sdk.amazonaws.com/java/api/latest/software/amazon/awssdk/services/s3/S3Configuration.Builder.html#pathStyleAccessEnabled(java.lang.Boolean)), может иметь значения `PATH` или `VIRTUAL_HOSTED`
    2.  Максимальное время выполнения операции
    3.  Проверять ли контрольную суммы [MD5 файлов перед загрузкой и при получении](https://sdk.amazonaws.com/java/api/latest/software/amazon/awssdk/services/s3/S3Configuration.Builder.html#checksumValidationEnabled(java.lang.Boolean)) из AWS
    4.  Кодировать ли в виде кусков при [подписании данных файла](https://sdk.amazonaws.com/java/api/latest/software/amazon/awssdk/services/s3/S3Configuration.Builder.html#chunkedEncodingEnabled(java.lang.Boolean)) при загрузке в AWS
    5.  Максимальный размер буфера при загрузке файлов (указывается как число в байтах / либо как `4MiB` / `4MB` / `1000Kb` и тп)
    6.  Максимальный размер кусочка файла при единовременной загрузке файла (указывается как число в байтах / либо как `4MiB` / `4MB` / `1000Kb` и тп)
    7.  URL хранилища S3
    8.  Ключ доступа к S3
    9.  Секрет доступа к S3
    10.  Регион хранилища S3
    11.  Включает логгирование модуля (по умолчанию `false`)
    12.  Включает метрики модуля (по умолчанию `true`)
    13.  Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) метрики
    14.  Включает трассировку модуля (по умолчанию `true`)

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
        telemetry:
          enabled: true #(14)!
    ```

    1.  Какой тип доступа к [файлам использовать](https://sdk.amazonaws.com/java/api/latest/software/amazon/awssdk/services/s3/S3Configuration.Builder.html#pathStyleAccessEnabled(java.lang.Boolean)), может иметь значения `PATH` или `VIRTUAL_HOSTED`
    2.  Максимальное время выполнения операции
    3.  Проверять ли контрольную суммы [MD5 файлов перед загрузкой и при получении](https://sdk.amazonaws.com/java/api/latest/software/amazon/awssdk/services/s3/S3Configuration.Builder.html#checksumValidationEnabled(java.lang.Boolean)) из AWS
    4.  Кодировать ли в виде кусков при [подписании данных файла](https://sdk.amazonaws.com/java/api/latest/software/amazon/awssdk/services/s3/S3Configuration.Builder.html#chunkedEncodingEnabled(java.lang.Boolean)) при загрузке в AWS
    5.  Максимальный размер буфера при загрузке файлов (указывается как число в байтах / либо как `4MiB` / `4MB` / `1000Kb` и тп)
    6.  Максимальный размер кусочка файла при единовременной загрузке файла (указывается как число в байтах / либо как `4MiB` / `4MB` / `1000Kb` и тп)
    7.  URL хранилища S3
    8.  Ключ доступа к S3
    9.  Секрет доступа к S3
    10.  Регион хранилища S3
    11.  Включает логгирование модуля (по умолчанию `false`)
    12.  Включает метрики модуля (по умолчанию `true`)
    13.  Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) метрики
    14.  Включает трассировку модуля (по умолчанию `true`)

Предоставляемые метрики модуля описаны в разделе [Справочник метрик](metrics.md#s3-клиент).

### Формат ответа

В случае использование AWS модуля, есть возможность получать специальные форматы ответа специфичные только AWS библиотеке:

| Операция                          | Формат ответа                                                                                                                                                                                                                                                                 |
|-----------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| [Получение файла](#_8)            | [GetObjectResponse](https://sdk.amazonaws.com/java/api/latest/software/amazon/awssdk/services/s3/model/GetObjectResponse.html) / [ResponseInputStream<GetObjectResponse>](https://sdk.amazonaws.com/java/api/latest/software/amazon/awssdk/core/ResponseInputStream.html)     |
| [Получение метаданных файла](#_9) | [HeadObjectResponse](https://sdk.amazonaws.com/java/api/latest/software/amazon/awssdk/services/s3/model/HeadObjectResponse.html)                                                                                                                                              |
| [Перечисление файлов](#_12)       | [ListObjectsV2Response](https://sdk.amazonaws.com/java/api/latest/software/amazon/awssdk/services/s3/model/ListObjectsV2Response.html)                                                                                                                                        |
| [Добавление файла](#_16)          | [PutObjectResponse](https://sdk.amazonaws.com/java/api/latest/software/amazon/awssdk/services/s3/model/PutObjectResponse.html)                                                                                                                                                |
| [Удаление файла](#_19)            | [DeleteObjectResponse](https://sdk.amazonaws.com/java/api/latest/software/amazon/awssdk/services/s3/model/DeleteObjectResponse.html) / [DeleteObjectsResponse](https://sdk.amazonaws.com/java/api/latest/software/amazon/awssdk/services/s3/model/DeleteObjectsResponse.html) |

## Minio

Реализация S3-клиента основанная на библиотеке [Minio](https://github.com/minio/minio-java).
Учитывайте что реализация использует [OkHttp](https://github.com/square/okhttp) написанный на Kotlin и использует соответствующие зависимости.

Для работы и внедрения доступны компоненты:

- Императивные [Kora S3 клиенты](#_23)
- `MinioClient` синхронный Minio S3 клиент
- `MinioAsyncClient` асинхронный Minio S3 клиент

### Подключение

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#_4) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora.experimental:s3-client-minio"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends MinioS3ClientModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#_4) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora.experimental:s3-client-minio")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : MinioS3ClientModule
    ```

Можно подключить [OkHttp модуль](http-client.md#okhttp) либо будет создан стандартный HTTP-клиент.

### Конфигурация

Пример полной конфигурации, описанной в классе `MinioS3ClientConfig` и `S3Config` (указаны примеры значений или значения по умолчанию):

===! ":material-code-json: `Hocon`"

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
            }
            tracing {
                enabled = true //(11)!
            }
        }
    }
    ```

    1.  Какой тип доступа к [файлам использовать](https://sdk.amazonaws.com/java/api/latest/software/amazon/awssdk/services/s3/S3Configuration.Builder.html#pathStyleAccessEnabled(java.lang.Boolean)), может иметь значения `PATH` или `VIRTUAL_HOSTED`
    2.  Максимальное время выполнения операции
    3.  Максимальный размер кусочка файла при единовременной загрузке файла (указывается как число в байтах / либо как `4MiB` / `4MB` / `1000Kb` и тп)
    4.  URL хранилища S3
    5.  Ключ доступа к S3
    6.  Секрет доступа к S3
    7.  Регион хранилища S3
    8.  Включает логгирование модуля (по умолчанию `false`)
    9.  Включает метрики модуля (по умолчанию `true`)
    10.  Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) метрики
    11.  Включает трассировку модуля (по умолчанию `true`)

=== ":simple-yaml: `YAML`"

    ```yaml
    s3client:
      minio:
        addressStyle: "PATH" #(1)!
        requestTimeout: "45s" #(1)!
        upload:
          partSize: "8MiB" #(2)!

      url: "http://localhost:9000" #(3)!
      accessKey: "someKey" #(4)!
      secretKey: "someSecret" #(5)!
      region: "aws-global" #(6)!
      telemetry:
        logging:
          enabled: false #(7)!
        metrics:
          enabled: true #(8)!
          slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(9)!
        telemetry:
          enabled: true #(10)!
    ```

    1.  Какой тип доступа к [файлам использовать](https://sdk.amazonaws.com/java/api/latest/software/amazon/awssdk/services/s3/S3Configuration.Builder.html#pathStyleAccessEnabled(java.lang.Boolean)), может иметь значения `PATH` или `VIRTUAL_HOSTED`
    2.  Максимальное время выполнения операции
    3.  Максимальный размер кусочка файла при единовременной загрузке файла (указывается как число в байтах / либо как `4MiB` / `4MB` / `1000Kb` и тп)
    4.  URL хранилища S3
    5.  Ключ доступа к S3
    6.  Секрет доступа к S3
    7.  Регион хранилища S3
    8.  Включает логгирование модуля (по умолчанию `false`)
    9.  Включает метрики модуля (по умолчанию `true`)
    10.  Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) метрики
    11.  Включает трассировку модуля (по умолчанию `true`)

## Клиент декларативный

Предлагается использовать специальные аннотации для создания декларативного клиента:

* `@S3.Client` — указывает что интерфейс является декларативным S3-клиентом
* `@S3.Get` — указывает что метод выполняет операцию [получения файла/метаданных](#_1)
* `@S3.List` — указывает что метод выполняет операцию [получения списка файлов/метаданных](#_1)
* `@S3.Put` — указывает что метод выполняет операцию [добавления файла](#_1)
* `@S3.Delete` — указывает что метод выполняет операцию [удаления файла](#_1)

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

### Конфигурация клиента

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

Пример конфигурации в случае пути `s3client.someClient` описанной в классе `S3ClientConfig`:

===! ":material-code-json: `Hocon`"

    ```javascript
    s3client {
        someClient {
            bucket = "someBucket" //(1)!
        }
    }
    ```

    1.  Корзина ([bucket](https://aws.amazon.com/ru/s3/faqs/)) где будут хранится файлы

=== ":simple-yaml: `YAML`"

    ```yaml
    s3client:
      someClient:
        bucket: "someBucket" #(1)!
    ```

    1.  Корзина ([bucket](https://aws.amazon.com/ru/s3/faqs/)) где будут хранится файлы

### Получение файла

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
    2. Получение в ответ файла вместе данными
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
    2. Получение в ответ файла вместе данными
    3. Ключ файла можно указать в аннотации

#### Метаданные

Операция получения файла по ключу может возвращать как полный файл вместе с данными `S3Object`,
так и облегченный вариант в виде метаданных файла без данных `S3ObjectMeta`,
такой метод значительно выполняется быстрее тк не возвращает данные файла.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient")
    public interface SomeClient {

        @S3.Get
        S3ObjectMeta operation(String key); //(1)!
    }
    ```

    1. Получение в ответ метаданные файла

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    interface SomeClient {

        @S3.Get
        fun operation(key: String): S3ObjectMeta //(1)!
    }
    ```

    1. Получение в ответ метаданные файла

#### Шаблон ключа

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

    1. Шаблон по которому собирать шаблон ключа, каждый аргумент шаблона будет подставлен через `toString()`, аргументы в шаблоне указывается как имена аргументов метода в `{ковычках}`
    2. Все аргументы метода должны быть частью шаблона ключа

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    interface SomeClient {

        @S3.Get("prefix-{key1}-{key2}-suffix") //(1)!
        fun operation(key1: String, key2: Int): S3Object //(2)!
    }
    ```

    1. Шаблон по которому собирать шаблон ключа, каждый аргумент шаблона будет подставлен через `toString()`, аргументы в шаблоне указывается как имена аргументов метода в `{ковычках}`
    2. Все аргументы метода должны быть частью шаблона ключа

#### Множество ключей

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

    1. Операция получения файла для множества ключей **не должна** содержать шаблон ключа
    2. Операция должна принимать список ключей и отдавать список `S3Object` либо `S3ObjectMeta`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    interface SomeClient {

        @S3.Get //(1)!
        fun operation(keys: List<String>): List<S3Object> //(2)!
    }
    ```

    1. Операция получения файла для множества ключей **не должна** содержать шаблон ключа
    2. Операция должна принимать список ключей и отдавать список `S3Object` либо `S3ObjectMeta`

### Перечисление файлов

Секция описывает операцию получения списка файлов/метаданных с помощью декларативного S3-клиента.
Предлагается использовать аннотацию `@S3.List` для указания операции.

Можно указывать [префикс ключа](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-prefixes.html), чтобы делать выборку по нужным ключам подходящим под префикс,
также можно указывать ограничение по выборке файлов, максимальное количество файлов для операции `1000`:

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
    3. Можно указывать ограничение по выборке файлов для операции перечисления, максимальное количество файлов для операции `1000`:

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
    3. Можно указывать ограничение по выборке файлов для операции перечисления, максимальное количество файлов для операции `1000`:

#### Метаданные

Операция получения файла по ключу может возвращать как полный файл вместе с данными `S3ObjectList`,
так и облегченный вариант в виде метаданных файла без данных `S3ObjectMetaList`,
такой метод значительно выполняется быстрее тк не возвращает данные файла.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient")
    public interface SomeClient {

        @S3.List
        S3ObjectMetaList operation(); //(1)!
    }
    ```

    1. Получение в ответ метаданные файлов

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    interface SomeClient {

        @S3.List
        fun operation(): S3ObjectMetaList //(1)!
    }
    ```

    1. Получение в ответ метаданные файлов

#### Шаблон префикса

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

    1. Шаблон по которому собирать шаблон префикса, каждый аргумент шаблона будет подставлен через `toString()`, аргументы в шаблоне указывается как имена аргументов метода в `{ковычках}`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    interface SomeClient {

        @S3.List("prefix-{key1}-{key2}-") //(1)!
        fun operation(key1: String, key2: Int): S3ObjectList
    }
    ```

    1. Шаблон по которому собирать шаблон префикса, каждый аргумент шаблона будет подставлен через `toString()`, аргументы в шаблоне указывается как имена аргументов метода в `{ковычках}`

#### Разделитель

Можно указывать разделитель для [префикса ключа](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-prefixes.html), исключать нужные файлы из выборки:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient")
    public interface SomeClient {

        @S3.List(value = "prefix/foo/bar", delimiter = "/") //(1)!
        S3ObjectList operation();
    }
    ```

    1. Указывается разделитель по которому будет фильтроваться перечисления файлов

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    interface SomeClient {

        @S3.List(value = "prefix/foo/bar", delimiter = "/") //(1)!
        fun operation(): S3ObjectList
    }
    ```

    1. Указывается разделитель по которому будет фильтроваться перечисления файлов

### Добавление файла

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

#### Тело файла

Тело файла (`S3Body`) может быть создано из `byte[]` / `ByteBuffer` / `InputStream` / `Flow.Publisher<ByteBuffer>` через соответсвующее статические методы конструкторы.

Если файл очень большой либо не известна его длина и требуется потоковая загрузка, то рекомендуется создавать тело с помощь `S3Body.ofPublisher()` либо `S3Body.ofInputStreamUnbound()`.

В случае если не будет указан тип файла, он будет проставлен как `application/octet-stream`.

#### Шаблон ключа

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

    1. Шаблон по которому собирать шаблон ключа, каждый аргумент шаблона будет подставлен через `toString()`, аргументы в шаблоне указывается как имена аргументов метода в `{ковычках}`
    2. Все аргументы метода должны быть частью шаблона ключа либо `S3Body`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    interface SomeClient {

        @S3.Put("prefix-{key1}-{key2}-suffix") //(1)!
        fun operation(key1: String, key2: Int, body: S3Body) //(2)!
    }
    ```

    1. Шаблон по которому собирать шаблон ключа, каждый аргумент шаблона будет подставлен через `toString()`, аргументы в шаблоне указывается как имена аргументов метода в `{ковычках}`
    2. Все аргументы метода должны быть частью шаблона ключа либо `S3Body`

### Удаление файла

Секция описывает операцию удаление файла с помощью декларативного S3-клиента.
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
    2. Получение в ответ файла вместе данными
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
    2. Получение в ответ файла вместе данными
    3. Ключ файла можно указать в аннотации

#### Шаблон ключа

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

    1. Шаблон по которому собирать шаблон ключа, каждый аргумент шаблона будет подставлен через `toString()`, аргументы в шаблоне указывается как имена аргументов метода в `{ковычках}`
    2. Все аргументы метода должны быть частью шаблона ключа

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    interface SomeClient {

        @S3.Delete("prefix-{key1}-{key2}-suffix") //(1)!
        fun operation(key1: String, key2: Int) //(2)!
    }
    ```

    1. Шаблон по которому собирать шаблон ключа, каждый аргумент шаблона будет подставлен через `toString()`, аргументы в шаблоне указывается как имена аргументов метода в `{ковычках}`
    2. Все аргументы метода должны быть частью шаблона ключа

#### Множество ключей

Можно также получать сразу множество файлов по ключам как полный файл вместе с данными `S3Object`,
так и облегченный вариант в виде множества метаданных файлов без данных `S3ObjectMeta`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient")
    public interface SomeClient {

        @S3.Delete //(1)!
        void operation(List<String> keys); //(2)!
    }
    ```

    1. Операция получения файла для множества ключей **не должна** содержать шаблон ключа
    2. Операция должна принимать список ключей и отдавать `void`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    interface SomeClient {

        @S3.Delete //(1)!
        fun operation(keys: List<String>) //(2)!
    }
    ```

    1. Операция получения файла для множества ключей **не должна** содержать шаблон ключа
    2. Операция должна принимать список ключей и отдавать `void`

### Сигнатуры

Доступные сигнатуры для методов декларативного HTTP клиента из коробки:

===! ":fontawesome-brands-java: `Java`"

    Под `T` подразумевается тип возвращаемого значения, либо `Void`.

    - `T myMethod()`
    - `CompletionStage<T> myMethod()` [CompletionStage](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/CompletionStage.html)
    - `Mono<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/) (надо подключить [зависимость](https://mvnrepository.com/artifact/io.projectreactor/reactor-core))

=== ":simple-kotlin: `Kotlin`"

    Под `T` подразумевается тип возвращаемого значения, либо `Unit`.

    - `myMethod(): T`
    - `suspend myMethod(): T` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine) (надо подключить [зависимость](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) как `implementation`)

## Клиент императивный

Можно внедрить императивный Kora клиента для работы с S3, предоставляется как клиент для синхронной так и асинхронной работы:

- `S3KoraClient` - клиент для синхронной работы
- `S3KoraAsyncClient` - клиент для асинхронной работы

## Ошибки

В случае ошибки работы клиента будут брошены специальные ошибки:

- `S3NotFoundException` - в случае если не найдет файл по указанному ключу
- `S3DeleteException` - в случае ошибки удаления файла
- `S3Exception` - в любом другом случае
