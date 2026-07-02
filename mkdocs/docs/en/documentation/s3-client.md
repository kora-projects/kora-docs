---
description: "Explains Kora S3 clients for AWS and Minio, declarative and imperative clients, file operations, metadata, key templates, and exception handling. Use when working with @S3.Client, @S3.Get, @S3.List, @S3.Put, @S3.Delete, S3ClientModule, AwsS3Client, MinioS3Client."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora S3 clients for AWS and Minio, declarative and imperative clients, file operations, metadata, key templates, and exception handling; key triggers include @S3.Client, @S3.Get, @S3.List, @S3.Put, @S3.Delete, S3ClientModule, AwsS3Client, MinioS3Client."
---

??? warning "Experimental module"

    **Experimental** module is fully working and tested, but requires additional approbation and usage analytics,
    therefore API may potentially undergo minor changes before it becomes fully stable.

The module provides an abstraction layer for working with [S3-compatible object storage](https://aws.amazon.com/s3/faqs/):
you can create declarative `S3` clients using annotations or inject ready-to-use imperative clients.
A declarative client is convenient for typical object and key operations, while an imperative client is useful when operations
need to be controlled directly in code.

For a step-by-step walkthrough before the reference details, see [S3](../guides/s3.md).

## AWS { #aws }

`S3` client implementation based on the [AWS library](https://github.com/aws/aws-sdk-java-v2).

Components available for injection:

- Imperative [Kora S3 clients](#client-imperative)
- `S3Client` synchronous AWS S3 client
- `S3AsyncClient` asynchronous AWS S3 client
- `S3AsyncClient` with tag `@Tag(MultipartUpload.class)` asynchronous AWS S3 client for batch uploading

### Dependency { #dependency }

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

### Configuration { #configuration }

Complete configuration described in the `AwsS3ClientConfig` and `S3Config` classes (example values or default values are specified):

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

    1.  Object access style, can have values `PATH` or `VIRTUAL_HOSTED` (default: `PATH`)
    2.  Maximum operation execution time (default: `45s`)
    3.  Whether to check the [MD5 checksum before upload and on retrieval](https://sdk.amazonaws.com/java/api/latest/software/amazon/awssdk/services/s3/S3Configuration.Builder.html#checksumValidationEnabled(java.lang.Boolean)) from `AWS` (default: `false`)
    4.  Whether to use chunked encoding when signing file data during upload to `AWS` (default: `true`)
    5.  Maximum buffer size for file uploads (default: `32MiB`)
    6.  Maximum file part size for a single file upload (default: `8MiB`)
    7.  `S3` storage `URL` (`required`, default is not specified)
    8.  `S3` access key (`required`, default is not specified)
    9.  `S3` access secret (`required`, default is not specified)
    10. `S3` storage region (default: `aws-global`)
    11. Enables module logging (default: `false`)
    12. Enables module metrics (default: `true`)
    13. Configures [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) for metrics (default: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    14. Configures metric tags (default: `{}`)
    15. Enables module tracing (default: `true`)
    16. Configures tracing attributes (default: `{}`)

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

    1.  Object access style, can have values `PATH` or `VIRTUAL_HOSTED` (default: `PATH`)
    2.  Maximum operation execution time (default: `45s`)
    3.  Whether to check the [MD5 checksum before upload and on retrieval](https://sdk.amazonaws.com/java/api/latest/software/amazon/awssdk/services/s3/S3Configuration.Builder.html#checksumValidationEnabled(java.lang.Boolean)) from `AWS` (default: `false`)
    4.  Whether to use chunked encoding when signing file data during upload to `AWS` (default: `true`)
    5.  Maximum buffer size for file uploads (default: `32MiB`)
    6.  Maximum file part size for a single file upload (default: `8MiB`)
    7.  `S3` storage `URL` (`required`, default is not specified)
    8.  `S3` access key (`required`, default is not specified)
    9.  `S3` access secret (`required`, default is not specified)
    10. `S3` storage region (default: `aws-global`)
    11. Enables module logging (default: `false`)
    12. Enables module metrics (default: `true`)
    13. Configures [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) for metrics (default: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    14. Configures metric tags (default: `{}`)
    15. Enables module tracing (default: `true`)
    16. Configures tracing attributes (default: `{}`)

Module metrics are described in the [Metrics Reference](metrics.md#s3-client) section.

### Response format { #response-format }

When using the `AWS` module, it is possible to return special response formats specific to the `AWS` library:

| Operation                      | Response format                                                                                                                                                                                                                                                               |
|--------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| [Get file](#get-file)          | [GetObjectResponse](https://sdk.amazonaws.com/java/api/latest/software/amazon/awssdk/services/s3/model/GetObjectResponse.html) / [ResponseInputStream<GetObjectResponse>](https://sdk.amazonaws.com/java/api/latest/software/amazon/awssdk/core/ResponseInputStream.html)     |
| [Get file metadata](#metadata) | [HeadObjectResponse](https://sdk.amazonaws.com/java/api/latest/software/amazon/awssdk/services/s3/model/HeadObjectResponse.html)                                                                                                                                              |
| [List files](#list-files)      | [ListObjectsV2Response](https://sdk.amazonaws.com/java/api/latest/software/amazon/awssdk/services/s3/model/ListObjectsV2Response.html)                                                                                                                                        |
| [Add file](#add-file)          | [PutObjectResponse](https://sdk.amazonaws.com/java/api/latest/software/amazon/awssdk/services/s3/model/PutObjectResponse.html)                                                                                                                                                |
| [Delete file](#delete-file)    | [DeleteObjectResponse](https://sdk.amazonaws.com/java/api/latest/software/amazon/awssdk/services/s3/model/DeleteObjectResponse.html) / [DeleteObjectsResponse](https://sdk.amazonaws.com/java/api/latest/software/amazon/awssdk/services/s3/model/DeleteObjectsResponse.html) |

For `@S3.Get` operations that retrieve an object or metadata, absence of an object can be described in the response type.
`Java` supports `Optional<S3Object>`, `Optional<S3ObjectMeta>`, `Optional<GetObjectResponse>`,
`Optional<ResponseInputStream<GetObjectResponse>>` and `Optional<HeadObjectResponse>`.
`Kotlin` uses nullable response types for this: `S3Object?`, `S3ObjectMeta?`, `GetObjectResponse?`,
`ResponseInputStream<GetObjectResponse>?` and `HeadObjectResponse?`.

## Minio { #minio }

`S3` client implementation based on the [Minio](https://github.com/minio/minio-java) library.
Note that the implementation uses [OkHttp](https://github.com/square/okhttp), written in `Kotlin`, and its dependencies.

Available components for injection:

- Imperative [Kora S3 clients](#client-imperative)
- `MinioClient` synchronous Minio S3 client
- `MinioAsyncClient` asynchronous Minio S3 client

### Dependency { #dependency-2 }

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

### Configuration { #configuration-2 }

Complete configuration described in the `MinioS3ClientConfig` and `S3Config` classes (example values or default values are specified):

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

    1. Object access style, can have values `PATH` or `VIRTUAL_HOSTED` (default: `PATH`)
    2. Maximum operation execution time (default: `45s`)
    3. Maximum file part size for a single file upload (default: `8MiB`)
    4. `S3` storage `URL` (`required`, default is not specified)
    5. `S3` access key (`required`, default is not specified)
    6. `S3` access secret (`required`, default is not specified)
    7. `S3` storage region (default: `aws-global`)
    8. Enables module logging (default: `false`)
    9. Enables module metrics (default: `true`)
    10. Configures [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) for metrics (default: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    11. Configures metric tags (default: `{}`)
    12. Enables module tracing (default: `true`)
    13. Configures tracing attributes (default: `{}`)

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

    1. Object access style, can have values `PATH` or `VIRTUAL_HOSTED` (default: `PATH`)
    2. Maximum operation execution time (default: `45s`)
    3. Maximum file part size for a single file upload (default: `8MiB`)
    4. `S3` storage `URL` (`required`, default is not specified)
    5. `S3` access key (`required`, default is not specified)
    6. `S3` access secret (`required`, default is not specified)
    7. `S3` storage region (default: `aws-global`)
    8. Enables module logging (default: `false`)
    9. Enables module metrics (default: `true`)
    10. Configures [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) for metrics (default: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    11. Configures metric tags (default: `{}`)
    12. Enables module tracing (default: `true`)
    13. Configures tracing attributes (default: `{}`)

## Client declarative { #client-declarative }

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

### Client Configuration { #client-configuration }

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

`@S3.Client` without arguments is equivalent to `@S3.Client("")`: the annotation `value` is empty,
and `S3ClientConfig` will be read from an empty path via `Config.get("")`.
In practice, it is usually better to specify an explicit path, for example `@S3.Client("s3client.someClient")`,
so that the `bucket` configuration is separated from other clients.

Configuration in the case of the `s3client.someClient` path described in the `S3ClientConfig` class:

===! ":material-code-json: `HOCON`"

    ```javascript
    s3client {
        someClient {
            bucket = "someBucket" //(1)!
        }
    }
    ```

    1.  Bucket ([bucket](https://aws.amazon.com/s3/faqs/)) where files will be stored (`required`, default is not specified)

=== ":simple-yaml: `YAML`"

    ```yaml
    s3client:
      someClient:
        bucket: "someBucket" #(1)!
    ```

    1.  Bucket ([bucket](https://aws.amazon.com/s3/faqs/)) where files will be stored (`required`, default is not specified)

#### Get file { #get-file }

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

#### Metadata { #metadata }

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

#### Key template { #key-template }

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

    1. Template used to build the key: each template argument is substituted via `toString()`, and template arguments are specified as method argument names in `{curly braces}`
    2. All method arguments must be part of the key template

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    interface SomeClient {

        @S3.Get("prefix-{key1}-{key2}-suffix") //(1)!
        fun operation(key1: String, key2: Int): S3Object //(2)!
    }
    ```

    1. Template used to build the key: each template argument is substituted via `toString()`, and template arguments are specified as method argument names in `{curly braces}`
    2. All method arguments must be part of the key template

#### Multiple keys { #multiple-keys }

It is also possible to retrieve multiple files by keys, either as complete objects with data (`S3Object`)
or as lightweight metadata without object data (`S3ObjectMeta`).

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient")
    public interface SomeClient {

        @S3.Get //(1)!
        List<S3Object> operation(List<String> keys); //(2)!
    }
    ```

    1. The get operation for multiple keys **must not** contain a key template
    2. The operation must accept a list of keys and return a list of `S3Object` or `S3ObjectMeta`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    interface SomeClient {

        @S3.Get //(1)!
        fun operation(keys: List<String>): List<S3Object> //(2)!
    }
    ```

    1. The get operation for multiple keys **must not** contain a key template
    2. The operation must accept a list of keys and return a list of `S3Object` or `S3ObjectMeta`

#### Optional response { #optional-get }

If absence of a file should not result in `S3NotFoundException`, the `@S3.Get` result can be made optional.
For standard `Kora` types, `Java` uses `Optional<S3Object>` and `Optional<S3ObjectMeta>`;
the `AWS` module also supports `Optional<GetObjectResponse>`,
`Optional<ResponseInputStream<GetObjectResponse>>` and `Optional<HeadObjectResponse>`.
`Kotlin` uses nullable response types for the same cases.

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

### List files { #list-files }

The section describes the operation to get a list of files/metadata using a declarative S3 client.
It is suggested that the `@S3.List` annotation be used to specify the operation.

You can specify a [key prefix](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-prefixes.html) to select keys matching that prefix,
and you can also set a file selection limit using the `limit` parameter of `@S3.List`.
The `limit` value must be in the `1..1000` range, and the default is `1000`.

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
    3. You can specify the file selection limit for the list operation via `limit`; the allowed range is `1..1000`, and the default is `1000`

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
    3. You can specify the file selection limit for the list operation via `limit`; the allowed range is `1..1000`, and the default is `1000`

#### Metadata { #metadata-2 }

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

#### Prefix template { #prefix-template }

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

    1. Template used to build the prefix: each template argument is substituted via `toString()`, and template arguments are specified as method argument names in `{curly braces}`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    interface SomeClient {

        @S3.List("prefix-{key1}-{key2}-") //(1)!
        fun operation(key1: String, key2: Int): S3ObjectList
    }
    ```

    1. Template used to build the prefix: each template argument is substituted via `toString()`, and template arguments are specified as method argument names in `{curly braces}`

#### Separator { #separator }

You can specify a delimiter for the [key prefix](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-prefixes.html) to filter the list result:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient")
    public interface SomeClient {

        @S3.List(value = "prefix/foo/bar", delimiter = "/") //(1)!
        S3ObjectList operation();
    }
    ```

    1. Delimiter used to filter file listing

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    interface SomeClient {

        @S3.List(value = "prefix/foo/bar", delimiter = "/") //(1)!
        fun operation(): S3ObjectList
    }
    ```

    1. Delimiter used to filter file listing

### Add file { #add-file }

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

#### File body { #file-body }

File body (`S3Body`) can be created from `byte[]`, `ByteBuffer`, `InputStream` or `Flow.Publisher<ByteBuffer>`
using the corresponding static factory methods. Every factory has overloads that additionally accept the
`type` (`Content-Type`) and `encoding` (`Content-Encoding`) values:

| Factory method                                | Source                       | Size       | Description                                                                                             |
|-----------------------------------------------|------------------------------|------------|--------------------------------------------------------------------------------------------------------|
| `S3Body.ofBytes(byte[])`                      | `byte[]`                     | Known      | Body from an in-memory byte array                                                                      |
| `S3Body.ofBuffer(ByteBuffer)`                 | `ByteBuffer`                 | Known      | Body from an in-memory buffer (uses `remaining()` as the size)                                          |
| `S3Body.ofInputStream(InputStream, long)`     | `InputStream`                | Known      | Streaming body whose exact length is passed explicitly as the `size` argument                          |
| `S3Body.ofInputStreamReadAll(InputStream)`    | `InputStream`                | Known      | Reads the whole stream into memory **immediately**, then behaves like a byte array                     |
| `S3Body.ofInputStreamUnbound(InputStream)`    | `InputStream`                | Unknown    | Streaming body of unknown length (`size()` returns `-1`)                                                |
| `S3Body.ofPublisher(Flow.Publisher)`          | `Flow.Publisher<ByteBuffer>` | Unknown    | Reactive streaming body of unknown length (`size()` returns `-1`)                                       |
| `S3Body.ofPublisher(Flow.Publisher, long)`    | `Flow.Publisher<ByteBuffer>` | Known      | Reactive streaming body whose length is passed explicitly as the `size` argument                       |

The body itself exposes the following accessors:

| Method                                      | Description                                                                       |
|---------------------------------------------|-----------------------------------------------------------------------------------|
| `byte[] asBytes()`                          | Reads the entire body into a byte array (drains the underlying stream)             |
| `InputStream asInputStream()`               | Returns the body as a blocking `InputStream`                                       |
| `Flow.Publisher<ByteBuffer> asPublisher()`  | Returns the body as a reactive `Flow.Publisher`                                    |
| `long size()`                               | Content length in bytes, or `-1` if unknown (unbound stream / publisher)           |
| `String type()`                             | `Content-Type` of the body                                                         |
| `String encoding()`                         | `Content-Encoding` of the body                                                     |

If the file is very large or its length is unknown and streaming is required, it is recommended to create the body using
`S3Body.ofPublisher(...)` or `S3Body.ofInputStreamUnbound(...)`.

If no file type is specified, `application/octet-stream` will be used.
For `@S3.Put`, the body can also be passed directly as `byte[]` or `ByteBuffer`; in that case the client creates `S3Body` itself.
The `@S3.Put` annotation allows specifying `type` and `encoding`, which will be written as `Content-Type` and `Content-Encoding`.

An `HTTP` server can stream a request body into `S3` without reading the whole file into memory first.
To do this, accept the request body as `Flow.Publisher<ByteBuffer>` and pass it to `S3Body.ofPublisher(...)`.
If the body size is known, for example from the `Content-Length` header, it is better to pass that size to `S3Body`;
if the size is unknown, use an overload without size and the size will be considered unknown.

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

In this variant, `Kora` obtains `Flow.Publisher<ByteBuffer>` from the `HTTP` request body through the standard
`HttpServerRequestMapper`, and the `S3` client reads the same stream during upload. The handler does not need to call
`asBytes()`, `asInputStream().readAllBytes()` or `S3Body.ofInputStreamReadAll(...)` if the goal is not to keep the whole file in memory.

#### Content type and encoding { #content-type }

Instead of constructing an `S3Body` yourself, you can pass the body directly as `byte[]` or `ByteBuffer` and let the client
wrap it into an `S3Body`. In that case the `type` (`Content-Type`) and `encoding` (`Content-Encoding`) attributes of `@S3.Put`
are used to build the body:

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

    1. `type` maps to `Content-Type` and `encoding` maps to `Content-Encoding`
    2. When the body is `byte[]` or `ByteBuffer`, the client builds the `S3Body` itself using the annotation's `type`/`encoding`
    3. If neither `type` nor `encoding` is set, `application/octet-stream` is used as the `Content-Type`

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

    1. `type` maps to `Content-Type` and `encoding` maps to `Content-Encoding`
    2. When the body is `ByteArray` or `ByteBuffer`, the client builds the `S3Body` itself using the annotation's `type`/`encoding`
    3. If neither `type` nor `encoding` is set, `application/octet-stream` is used as the `Content-Type`

!!! warning "Body type"

    The body of an `@S3.Put` operation must be `S3Body`, `byte[]` or `ByteBuffer`, otherwise a compilation error occurs.
    The `type` and `encoding` attributes only apply to raw `byte[]`/`ByteBuffer` bodies; when you pass a ready `S3Body`,
    its own `type()`/`encoding()` values are used and the annotation attributes are ignored.

#### Key template { #key-template-2 }

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

    1. Template used to build the key: each template argument is substituted via `toString()`, and template arguments are specified as method argument names in `{curly braces}`
    2. All method arguments must be part of the key template or be `S3Body`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    interface SomeClient {

        @S3.Put("prefix-{key1}-{key2}-suffix") //(1)!
        fun operation(key1: String, key2: Int, body: S3Body) //(2)!
    }
    ```

    1. Template used to build the key: each template argument is substituted via `toString()`, and template arguments are specified as method argument names in `{curly braces}`
    2. All method arguments must be part of the key template or be `S3Body`

### Delete file { #delete-file }

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
    2. File key to delete
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
    2. File key to delete
    3. The key of the file can be specified in the annotation

#### Key template { #key-template-3 }

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

    1. Template used to build the key: each template argument is substituted via `toString()`, and template arguments are specified as method argument names in `{curly braces}`
    2. All method arguments must be part of the key template

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    interface SomeClient {

        @S3.Delete("prefix-{key1}-{key2}-suffix") //(1)!
        fun operation(key1: String, key2: Int) //(2)!
    }
    ```

    1. Template used to build the key: each template argument is substituted via `toString()`, and template arguments are specified as method argument names in `{curly braces}`
    2. All method arguments must be part of the key template

#### Multiple keys { #multiple-keys-2 }

It is also possible to delete multiple files by keys.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient")
    public interface SomeClient {

        @S3.Delete //(1)!
        void operation(List<String> keys); //(2)!
    }
    ```

    1. The delete operation for multiple keys **must not** contain a key template
    2. The operation must accept a list of keys and return `void`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    interface SomeClient {

        @S3.Delete //(1)!
        fun operation(keys: List<String>) //(2)!
    }
    ```

    1. The delete operation for multiple keys **must not** contain a key template
    2. The operation must accept a list of keys and return `void`

### Signatures { #signatures }

Available signatures for declarative `S3` client methods out of the box:

===! ":fontawesome-brands-java: `Java`"

    The `T` refers to the type of the return value.

    - `T myMethod()`
    - `CompletionStage<T> myMethod()` [CompletionStage](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/CompletionStage.html)
    - `CompletableFuture<T> myMethod()` [CompletableFuture](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/CompletableFuture.html)
    - `Mono<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/) (require [dependency](https://mvnrepository.com/artifact/io.projectreactor/reactor-core))

=== ":simple-kotlin: `Kotlin`"

    By `T` we mean the type of the return value, either `T?`, or `Unit`.

    - `myMethod(): T`
    - `suspend myMethod(): T` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine) (require [dependency](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) as `implementation`)

## Models { #models }

Both declarative and imperative clients return the same set of model types (unless the `AWS` module's
[native response format](#response-format) is used). All models are read-only interfaces.

### S3Object { #model-s3-object }

Full object together with its data, returned by [get](#get-file) operations and available inside [S3ObjectList](#model-s3-object-list):

| Method              | Description                                                     |
|---------------------|-----------------------------------------------------------------|
| `String key()`      | Object key                                                       |
| `Instant modified()`| Last modification time                                          |
| `long size()`       | Object size in bytes                                            |
| `S3Body body()`     | Object [body](#file-body) with the data                        |

### S3ObjectMeta { #model-s3-object-meta }

Lightweight metadata without the object data, returned by metadata [get](#metadata) operations and available inside
[S3ObjectMetaList](#model-s3-object-meta-list). Retrieving metadata is faster because the object body is not transferred:

| Method               | Description                     |
|----------------------|---------------------------------|
| `String key()`       | Object key                      |
| `Instant modified()` | Last modification time          |
| `long size()`        | Object size in bytes            |

### S3ObjectList { #model-s3-object-list }

List of full objects returned by [list](#list-files) operations. Extends `S3ObjectMetaList`, so it also exposes the prefix and metadata:

| Method                        | Description                                       |
|-------------------------------|---------------------------------------------------|
| `String prefix()`             | Prefix used for the listing                        |
| `List<S3Object> objects()`    | Objects that matched the prefix (with data)        |
| `List<S3ObjectMeta> metas()`  | Metadata of the objects that matched the prefix    |

### S3ObjectMetaList { #model-s3-object-meta-list }

List of metadata returned by metadata [list](#metadata-2) operations:

| Method                        | Description                                     |
|-------------------------------|-------------------------------------------------|
| `String prefix()`             | Prefix used for the listing                      |
| `List<S3ObjectMeta> metas()`  | Metadata of the objects that matched the prefix  |

### S3ObjectUpload { #model-s3-object-upload }

Result of an [add file](#add-file) operation:

| Method                | Description                                                                 |
|-----------------------|-----------------------------------------------------------------------------|
| `String versionId()`  | Version identifier of the uploaded object (if bucket versioning is enabled) |

## Client imperative { #client-imperative }

It is possible to inject an imperative `Kora` client to work with `S3`; both synchronous and asynchronous clients are provided:

- `S3KoraClient` - client for synchronous operation
- `S3KoraAsyncClient` - client for asynchronous operation

Both clients work with explicit `bucket` and `key` parameters and support retrieving objects or metadata, listing objects by prefix,
uploading `S3Body`, and deleting one or more objects. Unlike the declarative client, they are not tied to a single `bucket` from
configuration — the `bucket` is passed to each method explicitly.

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

    1. Throws `S3NotFoundException` if the object is missing

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

    1. Throws `S3NotFoundException` if the object is missing

### Synchronous client { #client-imperative-sync }

The `S3KoraClient` interface provides the following operations:

| Method                                                                                | Description                                                        |
|---------------------------------------------------------------------------------------|-------------------------------------------------------------------|
| `S3Object get(bucket, key)`                                                           | Get a single object with data                                      |
| `S3ObjectMeta getMeta(bucket, key)`                                                   | Get metadata of a single object                                   |
| `List<S3Object> get(bucket, Collection<String> keys)`                                 | Get multiple objects with data                                    |
| `List<S3ObjectMeta> getMeta(bucket, Collection<String> keys)`                         | Get metadata of multiple objects                                  |
| `S3ObjectList list(bucket[, prefix[, delimiter, limit]])`                             | List objects by prefix (with data)                                |
| `S3ObjectMetaList listMeta(bucket[, prefix[, delimiter, limit]])`                     | List object metadata by prefix                                    |
| `List<S3ObjectList> list(bucket, Collection<String> prefixes[, delimiter, limit])`    | List objects for several prefixes at once                         |
| `List<S3ObjectMetaList> listMeta(bucket, Collection<String> prefixes[, delimiter, limit])` | List object metadata for several prefixes at once           |
| `S3ObjectUpload put(bucket, key, S3Body body)`                                        | Add an object and return the upload result                        |
| `void delete(bucket, key)`                                                            | Delete a single object                                            |
| `void delete(bucket, Collection<String> keys)`                                        | Delete multiple objects (throws `S3DeleteException` on failure)   |

The `list`/`listMeta` overloads without `delimiter`/`limit` default `delimiter` to `null` and `limit` to `1000`.
The `limit` argument must be in the `1..1000` range.

===! ":fontawesome-brands-java: `Java`"

    ```java
    // get a single object and its metadata
    S3Object object = s3.get("documents", "report.pdf");
    S3ObjectMeta meta = s3.getMeta("documents", "report.pdf");

    // get several objects at once
    List<S3Object> objects = s3.get("documents", List.of("a.pdf", "b.pdf"));

    // list by prefix with a delimiter and a limit
    S3ObjectList list = s3.list("documents", "2024/", "/", 100);
    for (S3Object o : list.objects()) {
        // ...
    }

    // list several prefixes at once
    List<S3ObjectMetaList> perPrefix = s3.listMeta("documents", List.of("2023/", "2024/"));

    // add an object
    S3ObjectUpload upload = s3.put("documents", "report.pdf", S3Body.ofBytes(bytes));
    String versionId = upload.versionId();

    // delete a single object and a batch of objects
    s3.delete("documents", "report.pdf");
    s3.delete("documents", List.of("a.pdf", "b.pdf"));
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // get a single object and its metadata
    val obj = s3.get("documents", "report.pdf")
    val meta = s3.getMeta("documents", "report.pdf")

    // get several objects at once
    val objects = s3.get("documents", listOf("a.pdf", "b.pdf"))

    // list by prefix with a delimiter and a limit
    val list = s3.list("documents", "2024/", "/", 100)
    for (o in list.objects()) {
        // ...
    }

    // list several prefixes at once
    val perPrefix = s3.listMeta("documents", listOf("2023/", "2024/"))

    // add an object
    val upload = s3.put("documents", "report.pdf", S3Body.ofBytes(bytes))
    val versionId = upload.versionId()

    // delete a single object and a batch of objects
    s3.delete("documents", "report.pdf")
    s3.delete("documents", listOf("a.pdf", "b.pdf"))
    ```

### Asynchronous client { #client-imperative-async }

The `S3KoraAsyncClient` interface mirrors `S3KoraClient` method-for-method, but every operation returns a
[CompletionStage](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/CompletionStage.html)
(`CompletionStage<Void>` for delete operations):

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

## Native clients { #native-clients }

Besides the declarative and imperative `Kora` clients, the underlying native `SDK` clients are also available for injection.
They are useful for advanced operations that are not covered by the declarative/imperative API (for example, bucket management,
object copying, presigned URLs, and so on).

The [AWS module](#aws) provides:

- `S3Client` — synchronous `AWS` client
- `S3AsyncClient` — asynchronous `AWS` client
- `S3AsyncClient` with `@Tag(MultipartUpload.class)` — asynchronous `AWS` client preconfigured for [multipart uploads](https://sdk.amazonaws.com/java/api/latest/software/amazon/awssdk/services/s3/internal/multipart/MultipartS3AsyncClient.html) according to `upload.partSize` and `upload.bufferSize`

The [Minio module](#minio) provides:

- `MinioClient` — synchronous `Minio` client
- `MinioAsyncClient` — asynchronous `Minio` client

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

    1. Native `AWS` `S3Client` injected directly
    2. Asynchronous client tagged with `@Tag(MultipartUpload.class)` for multipart uploads

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

    1. Native `AWS` `S3Client` injected directly
    2. Asynchronous client tagged with `@Tag(MultipartUpload::class)` for multipart uploads

## Exceptions { #exceptions }

If a client operation fails, one of the `S3` exceptions is thrown. All of them inherit from the base `S3Exception`,
which itself extends `RuntimeException`, so handling is optional and unchecked.

**Exception hierarchy:**

```
RuntimeException
└── S3Exception
    ├── S3NotFoundException
    └── S3DeleteException
```

The base `S3Exception` exposes the error code and message reported by the storage:

| Method                      | Description                                          |
|-----------------------------|------------------------------------------------------|
| `String getErrorCode()`     | Storage error code (for example, `NoSuchKey`)        |
| `String getErrorMessage()`  | Storage error message                                |

**Handling example:**

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
                // Object or bucket is missing: getErrorCode() is NoSuchKey or NoSuchBucket
            } catch (S3DeleteException e) {
                // One or more objects were not deleted
                for (S3DeleteException.Error error : e.getErrors()) {
                    // error.key(), error.bucket(), error.code(), error.message()
                }
            } catch (S3Exception e) {
                // Any other storage error: getErrorCode(), getErrorMessage()
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
                // Object or bucket is missing: errorCode is NoSuchKey or NoSuchBucket
            } catch (e: S3DeleteException) {
                // One or more objects were not deleted
                for (error in e.errors) {
                    // error.key(), error.bucket(), error.code(), error.message()
                }
            } catch (e: S3Exception) {
                // Any other storage error: errorCode, errorMessage
            }
        }
    }
    ```

### S3NotFoundException { #not-found-exception }

Thrown when a requested object or bucket does not exist.

**Causes:**

- Object key does not exist (`getErrorCode()` returns `NoSuchKey`)
- Bucket does not exist (`getErrorCode()` returns `NoSuchBucket`)

**Recommendations:**

- Make the `@S3.Get` result [optional](#optional-get) (`Optional`/nullable) if absence of an object is a normal outcome
- Verify the `bucket` from configuration and the requested `key`

### S3DeleteException { #delete-exception }

Thrown by batch `delete(bucket, keys)` operations when one or more objects could not be deleted.
It exposes the list of individual failures:

| Method               | Description                                                    |
|----------------------|----------------------------------------------------------------|
| `List<Error> getErrors()` | Per-object failures, each with `key()`, `bucket()`, `code()`, `message()` |

**Recommendations:**

- Inspect `getErrors()` to determine which objects failed and why
- Retry the failed keys separately if the failure is transient

### S3Exception { #base-exception }

Base exception thrown for any other storage or client error that is not a missing object or a batch-delete failure.

**Recommendations:**

- Log `getErrorCode()` and `getErrorMessage()` for diagnostics
- Enable client [logging](#configuration) at `DEBUG` level to inspect the underlying request/response

## Testing { #testing }

Declarative and imperative `S3` clients can be tested with [@KoraAppTest](junit5.md) together with a real
`S3`-compatible storage started in a [Testcontainers](https://java.testcontainers.org/) container (for example, `Minio`).
The storage connection parameters are supplied to the application config via system properties:

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
