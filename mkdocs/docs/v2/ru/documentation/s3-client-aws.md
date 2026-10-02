---
seo_title: "Интеграция Kora с AWS S3: клиент AWS SDK"
seo_description: "Настройка AWS SDK S3Client в Kora, совместное использование с декларативным S3-клиентом и администрирование бакетов."
keywords: ["Kora Framework", "фреймворк Kora", "AWS S3", "AWS SDK S3Client", "s3-client-aws", "объектное хранилище"]
description: "Explains the stable s3-client-aws integration, which publishes the AWS SDK S3Client in the Kora graph, configures it through s3client.aws and routes requests through Kora's HTTP client. Covers usage, configuration, combining it with the experimental declarative S3 client, and bucket administration."
agent:
  use_when: "Use this file for the stable AWS SDK S3 integration: s3-client-aws, AwsS3ClientModule, AwsS3Config, s3client.aws, software.amazon.awssdk.services.s3.S3Client, SDK operations, ExecutionInterceptor, combining both S3 artifacts, and bucket administration. For the experimental declarative Kora client, see s3-client.md."
---

Интеграция `s3-client-aws` не зависит от экспериментального [S3-клиента Kora](s3-client.md). Подключайте любой из артефактов отдельно или оба вместе, если нужны генерируемые операции с объектами и полный API AWS SDK.

## Клиент AWS SDK { #aws }

Артефакт `s3-client-aws` — это тонкая интеграция вокруг
[AWS SDK for Java v2](https://github.com/aws/aws-sdk-java-v2). Он публикует собственный клиент SDK
`software.amazon.awssdk.services.s3.S3Client` как компонент графа, настраивает его из конфигурации Kora
и направляет его `HTTP`-трафик через `HttpClient` Kora, чтобы таймауты и телеметрия оставались
согласованными с остальным приложением.

В нём **нет аннотаций `@S3` и нет моделей Kora S3** — работа с этим артефактом означает работу
с API AWS SDK. Используйте его для всего, что не покрывает декларативный контракт: администрирование
бакетов, копирование объектов, предподписанные URL, управление ACL и политиками, пакетное удаление.

### Подключение { #dependency }

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

### Конфигурация { #configuration }

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
    2. Пакетное удаление, которое [декларативный клиент](s3-client.md#delete-file) не генерирует

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
    2. Пакетное удаление, которое [декларативный клиент](s3-client.md#delete-file) не генерирует

Об ошибках сообщает собственная иерархия исключений SDK — `NoSuchKeyException`,
`NoSuchBucketException`, `S3Exception` — а не [исключения Kora `S3`](s3-client.md#exceptions).

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
    2.  Путь, объявленный в `@S3.Client("s3client.uploads")` [декларативного клиента](s3-client.md#client-declarative)

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
    2.  Путь, объявленный в `@S3.Client("s3client.uploads")` [декларативного клиента](s3-client.md#client-declarative)

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
