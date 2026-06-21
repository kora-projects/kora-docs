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
using the corresponding static factory methods: `ofBytes(...)`, `ofBuffer(...)`, `ofInputStream(...)`,
`ofInputStreamReadAll(...)`, `ofInputStreamUnbound(...)` and `ofPublisher(...)`.

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

## Client imperative { #client-imperative }

It is possible to inject an imperative `Kora` client to work with `S3`; both synchronous and asynchronous clients are provided:

- `S3KoraClient` - client for synchronous operation
- `S3KoraAsyncClient` - client for asynchronous operation

Both clients work with explicit `bucket` and `key` parameters and support retrieving objects or metadata, listing objects by prefix,
uploading `S3Body`, and deleting one or more objects.

## Exceptions { #exceptions }

Special errors will be thrown if a client operation error occurs:

- `S3NotFoundException` - if a file or bucket was not found
- `S3DeleteException` - in case of an error while deleting one or more files
- `S3Exception` - in any other case
