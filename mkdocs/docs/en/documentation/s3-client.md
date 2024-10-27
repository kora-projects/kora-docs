??? warning “Experimental module”

    **Experimental** module is fully working and tested, but does not guarantee a fully stabilized API and may undergo some minor changes before being fully ready.
    undergo some minor changes before being fully operational.

Module provides a thin layer of abstraction for creating S3-clients
using declarative-style annotations, or using imperative-style clients to work with [S3 storage](https://aws.amazon.com/s3/faqs/).

## AWS

S3 client implementation based on the [AWS library](https://github.com/aws/aws-sdk-java-v2).

Components available for injection:

- Imperative [Kora S3 clients](#client-imperative)
- `S3Client` synchronous AWS S3 client
- `S3AsyncClient` asynchronous AWS S3 client
- `S3AsyncClient` with tag `@Tag(MultipartUpload.class)` asynchronous AWS S3 client for batch uploading

### Dependency

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora.experimental:s3-client-aws"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends AwsS3ClientModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora.experimental:s3-client-aws")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : AwsS3ClientModule
    ```

Requires any [HTTP client](http-client.md) module to be added.

### Configuration

Complete configuration described in the `AwsS3ClientConfig` and `S3Config` classes (example values or default values are specified):

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

    1.  Which type of [file access to use](https://sdk.amazonaws.com/java/api/latest/software/amazon/awssdk/services/s3/S3Configuration.Builder.html#pathStyleAccessEnabled(java.lang.Boolean)), can have values `PATH` or `VIRTUAL_HOSTED`
    2.  The maximum execution time of the operation
    3.  Whether to check the checksum [MD5 of files before uploading and when retrieving](https://sdk.amazonaws.com/java/api/latest/software/amazon/awssdk/services/s3/S3Configuration.Builder.html#checksumValidationEnabled(java.lang.Boolean)) from AWS
    4.  Whether to encode in chunks when [signing file data](https://sdk.amazonaws.com/java/api/latest/software/amazon/awssdk/services/s3/S3Configuration.Builder.html#chunkedEncodingEnabled(java.lang.Boolean)) when uploading to AWS
    5.  Maximum buffer size when loading files (specified as a number in bytes / or as `4MiB` / `4MB` / `1000Kb` etc.)
    6.  Maximum file chunk size when loading a file at a time (specified as a number in bytes / or as `4MiB` / `4MB` / `1000Kb` etc.)
    7.  S3 storage URL
    8.  S3 access key
    9.  S3 access secret
    10.  S3 storage region
    11.  Enables module logging (default is `false`)
    12.  Enables module metrics (default is `true`)
    13.  Configures [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) for [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) metrics
    14.  Enables module tracing (default is `true`)

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

    1.  Which type of [file access to use](https://sdk.amazonaws.com/java/api/latest/software/amazon/awssdk/services/s3/S3Configuration.Builder.html#pathStyleAccessEnabled(java.lang.Boolean)), can have values `PATH` or `VIRTUAL_HOSTED`
    2.  The maximum execution time of the operation
    3.  Whether to check the checksum [MD5 of files before uploading and when retrieving](https://sdk.amazonaws.com/java/api/latest/software/amazon/awssdk/services/s3/S3Configuration.Builder.html#checksumValidationEnabled(java.lang.Boolean)) from AWS
    4.  Whether to encode in chunks when [signing file data](https://sdk.amazonaws.com/java/api/latest/software/amazon/awssdk/services/s3/S3Configuration.Builder.html#chunkedEncodingEnabled(java.lang.Boolean)) when uploading to AWS
    5.  Maximum buffer size when loading files (specified as a number in bytes / or as `4MiB` / `4MB` / `1000Kb` etc.)
    6.  Maximum file chunk size when loading a file at a time (specified as a number in bytes / or as `4MiB` / `4MB` / `1000Kb` etc.)
    7.  S3 storage URL
    8.  S3 access key
    9.  S3 access secret
    10.  S3 storage region
    11.  Enables module logging (default is `false`)
    12.  Enables module metrics (default is `true`)
    13.  Configures [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) for [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) metrics
    14.  Enables module tracing (default is `true`)

### Response format

When using AWS module, it is possible to return special response formats specific only to AWS library:

| Операция                    | Формат ответа                                                                                                                                                                                                                                                                 |
|-----------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| [Get file](#get-file)       | [GetObjectResponse](https://sdk.amazonaws.com/java/api/latest/software/amazon/awssdk/services/s3/model/GetObjectResponse.html) / [ResponseInputStream<GetObjectResponse>](https://sdk.amazonaws.com/java/api/latest/software/amazon/awssdk/core/ResponseInputStream.html)     |
| [List files](#list-files)   | [ListObjectsV2Response](https://sdk.amazonaws.com/java/api/latest/software/amazon/awssdk/services/s3/model/ListObjectsV2Response.html)                                                                                                                                        |
| [Add file](#add-file)       | [PutObjectResponse](https://sdk.amazonaws.com/java/api/latest/software/amazon/awssdk/services/s3/model/PutObjectResponse.html)                                                                                                                                                |
| [Delete file](#delete-file) | [DeleteObjectResponse](https://sdk.amazonaws.com/java/api/latest/software/amazon/awssdk/services/s3/model/DeleteObjectResponse.html) / [DeleteObjectsResponse](https://sdk.amazonaws.com/java/api/latest/software/amazon/awssdk/services/s3/model/DeleteObjectsResponse.html) |

## Minio

S3 client implementation based on [Minio](https://github.com/minio/minio-java) library.
Note that the implementation uses [OkHttp](https://github.com/square/okhttp) written in Kotlin and uses appropriate dependencies.

Available components for injection:

- Imperative [Kora S3 clients](#client-imperative)
- `MinioClient` synchronous Minio S3 client
- `MinioAsyncClient` asynchronous Minio S3 client

### Dependency

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora.experimental:s3-client-minio"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends MinioS3ClientModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora.experimental:s3-client-minio")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : MinioS3ClientModule
    ```

You can add [OkHttp module](http-client.md#okhttp) dependency or a standard HTTP client will be created automatically.

### Configuration

Complete configuration described in the `MinioS3ClientConfig` and `S3Config` classes (example values or default values are specified):

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

    1. Which type of [file access to use](https://sdk.amazonaws.com/java/api/latest/software/amazon/awssdk/services/s3/S3Configuration.Builder.html#pathStyleAccessEnabled(java.lang.Boolean)), can have values `PATH` or `VIRTUAL_HOSTED`
    2. Maximum execution time of the operation
    3. Maximum file chunk size for a single file upload (specified as a number in bytes / or as `4MiB` / `4MB` / `1000Kb` etc.)
    4. S3 storage URL
    5. S3 access key
    6. S3 access secret
    7. S3 storage region
    8. Enables module logging (default is `false`)
    9. Enables module metrics (default is `true`)
    10. Configures [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) for [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) metrics
    11. Enables module tracing (default is `true`)

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

    1. Which type of [file access to use](https://sdk.amazonaws.com/java/api/latest/software/amazon/awssdk/services/s3/S3Configuration.Builder.html#pathStyleAccessEnabled(java.lang.Boolean)), can have values `PATH` or `VIRTUAL_HOSTED`
    2. Maximum execution time of the operation
    3. Maximum file chunk size for a single file upload (specified as a number in bytes / or as `4MiB` / `4MB` / `1000Kb` etc.)
    4. S3 storage URL
    5. S3 access key
    6. S3 access secret
    7. S3 storage region
    8. Enables module logging (default is `false`)
    9. Enables module metrics (default is `true`)
    10. Configures [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) for [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) metrics
    11. Enables module tracing (default is `true`)

## Client declarative

It is suggested to use special annotations to create a declarative client:

* `@S3.Client` - indicates that the interface is a declarative S3 client
* `@S3.Get` - indicates that the method performs the [get file/metadata operation](#get-file)
* `@S3.List` - indicates that the method performs the [get file/metadata list operation](#list-files)
* `@S3.Put` - indicates that the method performs the [add file operation](#add-file)
* `@S3.Delete` - indicates that the method performs the [delete file operation](#delete-file)

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

### Client Configuration

Configuration of a particular implementation of `@S3.Client`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient") //(1)!
    public interface SomeClient {

        @S3.Get 
        S3Object operation(String key); 
    }
    ```

    1. Path to the configuration of this particular client

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient") //(1)!
    interface SomeClient {

        @S3.Get 
        fun operation(key: String): S3Object
    }
    ```

    1. Path to the configuration of this particular client

Configuration in the case of the `s3client.someClient` path described in the `S3ClientConfig` class:

===! ":material-code-json: `Hocon`"

    ```javascript
    s3client {
        someClient {
            bucket = "someBucket" //(1)!
        }
    }
    ```

    1.  Bucket ([bucket](https://aws.amazon.com/ru/s3/faqs/)) where files will be stored

=== ":simple-yaml: `YAML`"

    ```yaml
    s3client:
      someClient:
        bucket: "someBucket" #(1)!
    ```

    1.  Bucket ([bucket](https://aws.amazon.com/ru/s3/faqs/)) where files will be stored

#### Get file

Section describes the operation of getting a file/metadata using a declarative S3 client.
It is suggested to use the `@S3.Get` annotation to specify the operation.

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

    1. file retrieval operation
    2. file together with data in response
    3. key of the file can be specified in the annotation

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

    1. file retrieval operation
    2. file together with data in response
    3. key of the file can be specified in the annotation

#### Metadata

Get file by key operation can return either a complete file `S3Object` along with data,
or a lightweight version in the form of file metadata `S3ObjectMeta` without data,
this method is much faster because it does not return file data.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient")
    public interface SomeClient {

        @S3.Get
        S3ObjectMeta operation(String key); //(1)!
    }
    ```

    1. Receive file metadata in response

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    interface SomeClient {

        @S3.Get
        fun operation(key: String): S3ObjectMeta //(1)!
    }
    ```

    1. Receive file metadata in response

#### Key template

You can also specify a key as a template and substitute method arguments there as part of the template,
all method arguments must be part of the compound key.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient")
    public interface SomeClient {

        @S3.Get("prefix-{key1}-{key2}-suffix") //(1)!
        S3Object operation(String key1, int key2); //(2)!
    }
    ```

    1. template to build the key template, each template argument will be substituted via `toString()`, the arguments in the template are specified as method argument names in `{covens}`.
    2. All method arguments must be part of the key template

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    interface SomeClient {

        @S3.Get("prefix-{key1}-{key2}-suffix") //(1)!
        fun operation(key1: String, key2: Int): S3Object //(2)!
    }
    ```

    1. template to build the key template, each template argument will be substituted via `toString()`, the arguments in the template are specified as method argument names in `{covens}`.
    2. All method arguments must be part of the key template

#### Multiple keys

It is also possible to retrieve multiple files at once by key, either as a complete file along with the `S3Object` data,
or a lighter version as a set of metadata files without `S3ObjectMeta` data.

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

    1. The get file operation for multiple keys **must** not** contain a key pattern
    2. the operation must accept a list of keys and give a list of `S3Object` or `S3ObjectMeta`.

### List files

The section describes the operation to get a list of files/metadata using a declarative S3 client.
It is suggested that the `@S3.List` annotation be used to specify the operation.

You can specify [key prefix](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-prefixes.html) to sample the desired keys matching the prefix,
you can also specify a file selection limit, the maximum number of files for the operation is `1000`:

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

    1. prefix can be passed as a method argument if it is not specified in the annotation
    2. prefix can be specified in the annotation
    3. you can specify the file selection limit for the enumeration operation, the maximum number of files for the `1000` operation:

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

    1. prefix can be passed as a method argument if it is not specified in the annotation
    2. prefix can be specified in the annotation
    3. you can specify the file selection limit for the enumeration operation, the maximum number of files for the `1000` operation:

#### Metadata

Get file by key operation can return either a complete file `S3ObjectList` along with data,
or a lightweight version in the form of file metadata `S3ObjectMetaList` without data,
this method is much faster because it does not return file data.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient")
    public interface SomeClient {

        @S3.List
        S3ObjectMetaList operation(); //(1)!
    }
    ```

    1. Receive file metadata in response

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    interface SomeClient {

        @S3.List
        fun operation(): S3ObjectMetaList //(1)!
    }
    ```

    1. Receive file metadata in response

#### Prefix template

A prefix can also be specified as a template and method arguments can be substituted there as part of the template,
all method arguments must be part of a compound key.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient")
    public interface SomeClient {

        @S3.List("prefix-{key1}-{key2}-") //(1)!
        S3ObjectList operation(String key1, int key2);
    }
    ```

    1. template to build the prefix template, each template argument will be substituted via `toString()`, the arguments in the template are specified as method argument names in `{covens}`.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    interface SomeClient {

        @S3.List("prefix-{key1}-{key2}-") //(1)!
        fun operation(key1: String, key2: Int): S3ObjectList
    }
    ```

    1. template to build the prefix template, each template argument will be substituted via `toString()`, the arguments in the template are specified as method argument names in `{covens}`.

#### Separator

You can specify a delimiter for [key prefix](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-prefixes.html), to exclude required files from the sample:

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

    1. Specifies the delimiter by which the file enumeration will be filtered

### Add file

Section describes the operation of adding a file using a declarative S3 client.
It is suggested to use the `@S3.Put` annotation for the operation.

It is required to specify the key and body of the file to be added:

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

    1. File key by which it will be added to the repository
    2. file body itself, which will be added to the repository
    3. key can also be specified in the annotation if it is static

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

    1. File key by which it will be added to the repository
    2. file body itself, which will be added to the repository
    3. key can also be specified in the annotation if it is static

#### File body

File body (`S3Body`) can be created from `byte[]` / `ByteBuffer` / `InputStream` / `Flow.Publisher<ByteBuffer>` via the corresponding static constructor methods.

If the file is very large or its length is unknown and streaming is required, it is recommended to create the body using `S3Body.ofPublisher()` or `S3Body.ofInputStreamUnbound()`.

If no file type is specified, it will be set as `application/octet-stream`.

#### Key template

Key can also be specified as a template and method arguments can be substituted there as part of the template,
all method arguments must be part of a compound key.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient")
    public interface SomeClient {

        @S3.Put("prefix-{key1}-{key2}-suffix") //(1)!
        void operation(String key1, int key2, S3Body body); //(2)!
    }
    ```

    1. template to build the key template, each template argument will be substituted via `toString()`, the arguments in the template are specified as method argument names in `{covens}`.
    2. All method arguments must be part of the key template either `S3Body`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    interface SomeClient {

        @S3.Put("prefix-{key1}-{key2}-suffix") //(1)!
        fun operation(key1: String, key2: Int, body: S3Body) //(2)!
    }
    ```

    1. template to build the key template, each template argument will be substituted via `toString()`, the arguments in the template are specified as method argument names in `{covens}`.
    2. All method arguments must be part of the key template either `S3Body`

### Delete file

Section describes the operation of deleting a file using a declarative S3 client.
It is suggested to use the `@S3.Delete` annotation for the operation.

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

    1. file deletion operation
    2. Receiving a file with data in response
    3. The key of the file can be specified in the annotation

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

    1. file deletion operation
    2. Receiving a file with data in response
    3. The key of the file can be specified in the annotation

#### Key template

Key can also be specified as a template and method arguments can be substituted there as part of the template,
all method arguments must be part of the composite key.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient")
    public interface SomeClient {

        @S3.Delete("prefix-{key1}-{key2}-suffix") //(1)!
        void operation(String key1, int key2); //(2)!
    }
    ```

    1. template to build the key template, each template argument will be substituted via `toString()`, the arguments in the template are specified as method argument names in `{covens}`.
    2. All method arguments must be part of the key template

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    interface SomeClient {

        @S3.Delete("prefix-{key1}-{key2}-suffix") //(1)!
        fun operation(key1: String, key2: Int) //(2)!
    }
    ```

    1. template to build the key template, each template argument will be substituted via `toString()`, the arguments in the template are specified as method argument names in `{covens}`.
    2. All method arguments must be part of the key template

#### Multiple keys

It is also possible to retrieve multiple files at once by key, either as a complete file along with the `S3Object` data,
or a lighter version as a set of metadata files without `S3ObjectMeta` data.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient")
    public interface SomeClient {

        @S3.Delete //(1)!
        void operation(List<String> keys); //(2)!
    }
    ```

    1. a get file operation for multiple keys **must** not** contain a key pattern
    2. the operation must accept a list of keys and return `void`.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    interface SomeClient {

        @S3.Delete //(1)!
        fun operation(keys: List<String>) //(2)!
    }
    ```

    1. a get file operation for multiple keys **must** not** contain a key pattern
    2. the operation must accept a list of keys and return `void`.

### Signatures

Available signatures for repository methods out of the box:

===! ":fontawesome-brands-java: `Java`"

    The `T` refers to the type of the return value.

    - `T myMethod()`
    - `CompletionStage<T> myMethod()` [CompletionStage](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/CompletionStage.html)
    - `Mono<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/) (require [dependency](https://mvnrepository.com/artifact/io.projectreactor/reactor-core))

=== ":simple-kotlin: `Kotlin`"

    By `T` we mean the type of the return value, either `T?`, or `Unit`.

    - `myMethod(): T`
    - `suspend myMethod(): T` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine) (require [dependency](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) as `implementation`)

## Client imperative

It is possible to implement an imperative Kora client to work with S3, both synchronous and asynchronous clients are provided:

- `S3KoraClient` - client for synchronous operation
- `S3KoraAsyncClient` - client for asynchronous operation.

## Exceptions

Special errors will be thrown if a client operation error occurs:

- `S3NotFoundException` - in case it does not find a file by the specified key
- `S3DeleteException` - in case of file deletion error
- `S3Exception` - in any other case
