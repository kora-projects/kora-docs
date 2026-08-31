---
description: "Explains the two independent Kora S3 artifacts: the declarative s3-client-kora client built on Kora's own HTTP client and the s3-client-aws wrapper that publishes the AWS SDK S3Client. Covers @S3.Client, @S3.Bucket, @S3.Get, @S3.Head, @S3.List, @S3.Put, @S3.Delete, request arguments, response models, configuration, exceptions and testing."
agent:
  use_when: "Use this file for Kora docs or implementation questions about S3-compatible object storage: choosing between s3-client-kora and s3-client-aws, declarative clients, bucket and credentials resolution, key templates, multipart upload, byte ranges and exception handling; key triggers include @S3.Client, @S3.Bucket, @S3.Get, @S3.Head, @S3.List, @S3.Put, @S3.Delete, KoraS3ClientModule, AwsS3ClientModule, S3ClientConfig, AwsS3Config, S3ClientFactory, GetObjectResult, HeadObjectResult, ListBucketResult, S3ClientNoSuchKeyException."
---

Kora ships **two independent S3 artifacts**. They share nothing but the protocol they speak: different
Maven coordinates, different packages, different configuration sections, different APIs.
Pick the one that matches the way you want to work with [S3-compatible object storage](https://aws.amazon.com/s3/faqs/),
or add both if you need both.

| Artifact                                        | What you get                                                                                                            | Use it when                                                                            |
|-------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------|
| `io.koraframework.experimental:s3-client-kora`  | Declarative `@S3.Client` interfaces and the imperative `S3Client` contract, implemented on top of Kora's own HTTP client | You want compile-time generated, telemetry-aware clients for object operations           |
| `io.koraframework:s3-client-aws`                | The AWS SDK `software.amazon.awssdk.services.s3.S3Client` published as a graph component                                 | You want the full AWS SDK surface: bucket administration, copying, presigned URLs, ACLs |

!!! warning "Two different `S3Client` types"

    Both artifacts expose a type named `S3Client`, and they are unrelated:
    `io.koraframework.s3.client.kora.S3Client` is the Kora imperative contract, while
    `software.amazon.awssdk.services.s3.S3Client` is the AWS SDK client. Import the right one —
    mixing them up produces confusing "no factory found" graph build errors.

If a wrong artifact is on the classpath, compilation fails with messages like
`package S3 does not exist` or `package io.koraframework.s3.client.model does not exist`:
the `@S3` annotations and all model types live only in `s3-client-kora`.

For a step-by-step walkthrough before the reference details, see [S3](../guides/s3.md).

## Kora client { #kora }

??? warning "Experimental module"

    **Experimental** module is fully working and tested, but requires additional approbation and usage analytics,
    therefore API may potentially undergo minor changes before it becomes fully stable.

The `s3-client-kora` artifact implements the S3 REST API directly on Kora's own [HTTP client](http-client.md).
It provides declarative `@S3.Client` interfaces, the imperative `S3Client` contract, request/response models
and telemetry. It does **not** depend on the AWS SDK.

### Dependency { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "io.koraframework.experimental:s3-client-kora"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends KoraS3ClientModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("io.koraframework.experimental:s3-client-kora")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : KoraS3ClientModule
    ```

Requires any [HTTP client](http-client.md) module to be added, because the S3 client executes its requests
through the `HttpClient` component from the graph — for example
[Apache HttpClient](http-client.md#apache-httpclient), [OkHttp](http-client.md#okhttp)
or the [native JDK client](http-client.md#native-client).

### Configuration { #configuration }

Each declarative client reads its own `S3ClientConfig` from the path declared in
[`@S3.Client`](#client-configuration). Basic parameters:

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

    1.  Endpoint `URL` of the `S3` storage (`required`, no default)
    2.  `S3` access key (`required` unless every client method takes an [`S3Credentials`](#credentials) argument)
    3.  `S3` secret key (`required` unless every client method takes an [`S3Credentials`](#credentials) argument)
    4.  `S3` storage region (default: `aws-global`)

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

    1.  Endpoint `URL` of the `S3` storage (`required`, no default)
    2.  `S3` access key (`required` unless every client method takes an [`S3Credentials`](#credentials) argument)
    3.  `S3` secret key (`required` unless every client method takes an [`S3Credentials`](#credentials) argument)
    4.  `S3` storage region (default: `aws-global`)

??? note "Full Configuration"

    Complete configuration described in the `S3ClientConfig` and `S3ClientConfigWithCredentials` classes
    (example values or default values are specified):

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

        1.  Endpoint `URL` of the `S3` storage (`required`, no default)
        2.  `S3` access key (`required` unless every client method takes an [`S3Credentials`](#credentials) argument)
        3.  `S3` secret key (`required` unless every client method takes an [`S3Credentials`](#credentials) argument)
        4.  `S3` storage region, used for request signing (default: `aws-global`)
        5.  Object access style, can have values `PATH` or `VIRTUAL_HOSTED` (default: `PATH`)
        6.  Maximum operation execution time, passed to the underlying `HTTP` request (default: `45s`)
        7.  Part size used when a [multipart upload](#multipart-upload) is performed for an `InputStream` body (default: `5MiB`)
        8.  Chunk size used by `aws-chunked` encoding when the body is a [`ContentWriter`](#file-body) (default: `64KiB`)
        9.  Object size from which a multipart upload is preferred over a single-request upload (default: `100MiB`)
        10. Enables module logging (default: `false`)
        11. Enables module metrics (default: `false`)
        12. Configures [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) for metrics (default: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
        13. Configures metric tags (default: `{}`)
        14. Enables module tracing (default: `true`)
        15. Configures tracing attributes (default: `{}`)

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

        1.  Endpoint `URL` of the `S3` storage (`required`, no default)
        2.  `S3` access key (`required` unless every client method takes an [`S3Credentials`](#credentials) argument)
        3.  `S3` secret key (`required` unless every client method takes an [`S3Credentials`](#credentials) argument)
        4.  `S3` storage region, used for request signing (default: `aws-global`)
        5.  Object access style, can have values `PATH` or `VIRTUAL_HOSTED` (default: `PATH`)
        6.  Maximum operation execution time, passed to the underlying `HTTP` request (default: `45s`)
        7.  Part size used when a [multipart upload](#multipart-upload) is performed for an `InputStream` body (default: `5MiB`)
        8.  Chunk size used by `aws-chunked` encoding when the body is a [`ContentWriter`](#file-body) (default: `64KiB`)
        9.  Object size from which a multipart upload is preferred over a single-request upload (default: `100MiB`)
        10. Enables module logging (default: `false`)
        11. Enables module metrics (default: `false`)
        12. Configures [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) for metrics (default: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
        13. Configures metric tags (default: `{}`)
        14. Enables module tracing (default: `true`)
        15. Configures tracing attributes (default: `{}`)

The `bucket` name is **not** part of `S3ClientConfig`. It is resolved separately through
[`@S3.Bucket`](#bucket), which may point at any configuration path.

Module metrics are described in the [Metrics Reference](metrics.md#s3-client) section.

## Declarative client { #client-declarative }

Special annotations are used to create a declarative client:

* `@S3.Client` — marks the interface as a declarative S3 client
* `@S3.Bucket` — declares where the [bucket name](#bucket) comes from
* `@S3.Get` — the method performs the [get object](#get-file) operation
* `@S3.Head` — the method performs the [get object metadata](#metadata) operation
* `@S3.List` — the method performs the [list objects](#list-files) operation
* `@S3.Put` — the method performs the [add object](#add-file) operation
* `@S3.Delete` — the method performs the [delete object](#delete-file) operation

All annotations live in `io.koraframework.s3.client.kora.annotation`.
Exactly one operation annotation per method is allowed.

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

`@S3.Client` may only be placed on an interface; the processor rejects classes with a
`@S3.Client can only be applied to an interface` error.

### Client configuration { #client-configuration }

The `value` of `@S3.Client` is the configuration path from which [`S3ClientConfig`](#configuration) is read:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient") //(1)!
    @S3.Bucket(".bucket")
    public interface SomeClient {

        @S3.Get
        GetObjectResult operation(String key);
    }
    ```

    1. Path to the configuration of this particular client

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient") //(1)!
    @S3.Bucket(".bucket")
    interface SomeClient {

        @S3.Get
        fun operation(key: String): GetObjectResult
    }
    ```

    1. Path to the configuration of this particular client

!!! warning "Client path without a value"

    `@S3.Client` without a value does **not** mean "the root of the configuration".
    The processor falls back to the **simple name of the interface**, so `@S3.Client` on
    `interface SomeClient` reads its configuration from the `SomeClient` path. Always declare an explicit
    path such as `@S3.Client("s3client.someClient")` — it keeps each client's settings separated and
    makes the configuration file readable.

Every client gets its own configuration section, so two clients can talk to two different storages
in one application:

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

### Bucket { #bucket }

The bucket name is never taken from the client configuration implicitly — it is always declared
through `@S3.Bucket`. There are three ways to provide it, checked in this order:

1. A method parameter annotated with `@S3.Bucket` — the bucket is a runtime value
2. `@S3.Bucket("config.path")` on the method — the bucket is read from configuration for that method
3. `@S3.Bucket("config.path")` on the interface — the bucket is read from configuration for every method

A path that starts with a dot is **relative to the client path** declared in `@S3.Client`;
a path without a leading dot is an absolute path in the configuration.

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

    1. Relative path: resolves to `s3client.someClient.bucket`
    2. Absolute path: resolves to `s3client.archive.bucket`
    3. Bucket passed at runtime; the parameter is not part of the [object key](#key-template)

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

    1. Relative path: resolves to `s3client.someClient.bucket`
    2. Absolute path: resolves to `s3client.archive.bucket`
    3. Bucket passed at runtime; the parameter is not part of the [object key](#key-template)

Configuration for the example above:

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

    1.  Read by `@S3.Bucket(".bucket")`
    2.  Read by `@S3.Bucket("s3client.archive.bucket")`

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

    1.  Read by `@S3.Bucket(".bucket")`
    2.  Read by `@S3.Bucket("s3client.archive.bucket")`

!!! warning "Bucket is required"

    A method with no bucket source at all fails at compile time with
    `S3 operation '...' has no bucket source`. `@S3.Bucket` used without a value on a type or a method
    fails with `S3 bucket config path is missing`: an empty value is only meaningful on a parameter.

!!! note "Bucket name is generated, not injected"

    A configured bucket name ends up in a generated `$SomeClient_BucketsConfig` class, not in an
    injectable component. Code that needs the same bucket name elsewhere — a bucket initializer, for
    example — reads the same configuration path itself with [`@ConfigSource`](config.md), see
    [Bucket administration](#bucket-administration).

### Credentials { #credentials }

By default credentials come from the `credentials` section of the client configuration.
A method may instead accept an `S3Credentials` parameter and sign that single call with it:

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

    1. Uses `credentials { accessKey, secretKey }` from the client configuration
    2. Uses the credentials passed at runtime; the parameter is not part of the object key

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

    1. Uses `credentials { accessKey, secretKey }` from the client configuration
    2. Uses the credentials passed at runtime; the parameter is not part of the object key

An `S3Credentials` value is created with the static factory:

===! ":fontawesome-brands-java: `Java`"

    ```java
    S3Credentials credentials = S3Credentials.of("someKey", "someSecret");
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val credentials = S3Credentials.of("someKey", "someSecret")
    ```

The client configuration type is chosen by the processor: if **every** method of the interface takes an
`S3Credentials` parameter, the client is bound to `S3ClientConfig` and the `credentials` section is not
required at all. If at least one method does not, the client is bound to `S3ClientConfigWithCredentials`
and `credentials { accessKey, secretKey }` becomes `required`.

### Get file { #get-file }

Section describes the operation of getting an object using a declarative S3 client.
It is suggested to use the `@S3.Get` annotation to specify the operation.

The return type is either [`GetObjectResult`](#model-get-object-result) — the raw response whose body
is read as a stream — or `byte[]` / `ByteArray`, in which case the client reads the whole body into
memory and closes the response for you.

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

    1. Object retrieval operation
    2. Full response with a streaming body; the caller must close it
    3. Whole object read into memory, the response is closed by the client
    4. Key of the object can be specified in the annotation

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

    1. Object retrieval operation
    2. Full response with a streaming body; the caller must close it
    3. Whole object read into memory, the response is closed by the client
    4. Key of the object can be specified in the annotation

`GetObjectResult` is an `HttpClientResponse` and therefore `Closeable`. Reading its body means closing
both the response and the body:

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

Any other return type is a compile-time error:
`S3 operation '@S3.Get' on method '...' has unsupported return type`.

#### Key template { #key-template }

A key can be specified as a template, and method arguments are substituted into it,
all key arguments of the method must be part of the template.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient")
    @S3.Bucket(".bucket")
    public interface SomeClient {

        @S3.Get("prefix-{key1}-{key2}-suffix") //(1)!
        GetObjectResult operation(String key1, int key2); //(2)!
    }
    ```

    1. Template used to build the key: each template argument is substituted via `String.valueOf()`, and template arguments are specified as method argument names in `{curly braces}`
    2. All key arguments of the method must be part of the key template

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    @S3.Bucket(".bucket")
    interface SomeClient {

        @S3.Get("prefix-{key1}-{key2}-suffix") //(1)!
        fun operation(key1: String, key2: Int): GetObjectResult //(2)!
    }
    ```

    1. Template used to build the key: each template argument is substituted via `String.valueOf()`, and template arguments are specified as method argument names in `{curly braces}`
    2. All key arguments of the method must be part of the key template

Parameters that are **not** key parts and therefore never appear in the template:

- a parameter annotated with [`@S3.Bucket`](#bucket)
- a parameter of type [`S3Credentials`](#credentials)
- a parameter of an [argument type](#model-request-args) — `GetObjectArgs`, `HeadObjectArgs`, `ListObjectsArgs`, `PutObjectArgs`, `DeleteObjectArgs`
- a [body](#file-body) parameter — `byte[]`, `ByteBuffer`, `InputStream`, `S3Client.ContentWriter`

Without a template, the method must have exactly one key parameter and its `String.valueOf()` becomes
the key. The processor rejects the ambiguous cases with explicit messages:

| Situation                                        | Compile-time error                                                          |
|--------------------------------------------------|------------------------------------------------------------------------------|
| Several key parameters and no template            | `has N key parameters, but no key template`                                  |
| No key parameter and no constant key              | `has no object key`                                                          |
| A template that references an unknown parameter   | `references key template parameter '{x}', but the method has no matching key parameter` |
| A template without a closing brace                | `has malformed key template ...: missing closing '}'`                        |
| A collection or map used as a template parameter  | `uses '{x}' in the key template, but parameter 'x' is a collection or map`   |
| A collection used as the single key parameter     | `expects one object key, but parameter 'x' is a collection`                  |

#### Optional response { #optional-get }

If the absence of an object is a normal outcome rather than an error, mark the method as nullable.
`Java` uses the [JSpecify](https://jspecify.dev) `@Nullable` annotation, `Kotlin` uses a nullable return
type. A nullable operation returns `null` instead of throwing [`S3ClientNoSuchKeyException`](#not-found-exception).

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

    1. A nullable return type turns the operation into an optional one

The same applies to `byte[]` / `ByteArray` results of `@S3.Get`.

#### Request arguments { #get-args }

An operation may accept an [argument object](#model-request-args) that carries everything the S3 API
supports beyond the bucket and the key — conditional headers, a version id, response header overrides,
server-side encryption parameters and a [byte range](#range):

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient")
    @S3.Bucket(".bucket")
    public interface SomeClient {

        @S3.Get("prefix-{key}")
        GetObjectResult operation(String key, GetObjectArgs args); //(1)!
    }
    ```

    1. The `GetObjectArgs` parameter is passed to the S3 request as is and is not part of the key

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    @S3.Bucket(".bucket")
    interface SomeClient {

        @S3.Get("prefix-{key}")
        fun operation(key: String, args: GetObjectArgs): GetObjectResult //(1)!
    }
    ```

    1. The `GetObjectArgs` parameter is passed to the S3 request as is and is not part of the key

Argument objects are mutable holders with public fields:

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

#### Byte range { #range }

`GetObjectArgs` and `HeadObjectArgs` accept a `Range` that maps to the
[HTTP `Range` header](https://www.rfc-editor.org/rfc/rfc9110.html#name-range). `Range` is a sealed
interface with three factories:

| Factory                            | Meaning                                                          | Header value        |
|------------------------------------|------------------------------------------------------------------|---------------------|
| `Range.fromTo(first, last)`        | Bytes from `first` to `last`, both inclusive                      | `bytes=first-last`  |
| `Range.from(first)`                | Bytes from `first` to the end of the object                       | `bytes=first-`      |
| `Range.last(bytes)`                | The last `bytes` bytes of the object                              | `bytes=-bytes`      |

===! ":fontawesome-brands-java: `Java`"

    ```java
    var args = new GetObjectArgs();
    args.range = Range.fromTo(0, 1023); //(1)!

    try (var response = client.operation("video.mp4", args)) {
        var range = response.contentRange(); //(2)!
    }
    ```

    1. First kilobyte of the object
    2. `ContentRange(firstPosition, lastPosition, completeLength)` parsed from the `Content-Range` header

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val args = GetObjectArgs()
    args.range = Range.fromTo(0, 1023) //(1)!

    client.operation("video.mp4", args).use { response ->
        val range = response.contentRange() //(2)!
    }
    ```

    1. First kilobyte of the object
    2. `ContentRange(firstPosition, lastPosition, completeLength)` parsed from the `Content-Range` header

### Metadata { #metadata }

The `@S3.Head` operation retrieves object metadata without transferring the object body,
which makes it much cheaper than a [get](#get-file). The only supported return type is
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

    1. Metadata retrieval operation
    2. Key of the object can be specified in the annotation
    3. Supports the same [argument object](#model-request-args) mechanics as `@S3.Get`

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

    1. Metadata retrieval operation
    2. Key of the object can be specified in the annotation
    3. Supports the same [argument object](#model-request-args) mechanics as `@S3.Get`

!!! note "HEAD has no response body"

    `S3` answers a `HEAD` request for a missing object with `404` and an empty body, so the storage
    error code cannot be read. A missing object and a missing bucket both surface as a
    [`S3ClientNoSuchKeyException`](#not-found-exception)-shaped failure with `errorCode` `NoSuchKey` —
    do not use `@S3.Head` to distinguish the two.

### List files { #list-files }

The section describes the operation to list objects using a declarative S3 client.
It is suggested that the `@S3.List` annotation be used to specify the operation.

The [key prefix](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-prefixes.html) can be a
constant in the annotation, a template built from method arguments, or a field of a
[`ListObjectsArgs`](#list-args) parameter.

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

    1. Prefix passed as a method argument when it is not specified in the annotation
    2. Constant prefix specified in the annotation
    3. Prefix built from a [template](#prefix-template)

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

    1. Prefix passed as a method argument when it is not specified in the annotation
    2. Constant prefix specified in the annotation
    3. Prefix built from a [template](#prefix-template)

Supported return types:

| Return type                                     | Description                                                                            |
|-------------------------------------------------|----------------------------------------------------------------------------------------|
| `ListBucketResult`                              | One page of the listing, together with `keyCount`, `commonPrefixes` and the continuation token |
| `List<ListBucketResult.ListBucketItem>`         | Items of one page                                                                       |
| `List<String>`                                  | Keys of one page                                                                        |
| `Iterator<ListBucketResult.ListBucketItem>`     | [Lazy iterator](#list-iterator) over all pages                                          |
| `Iterator<String>`                              | [Lazy iterator](#list-iterator) over keys of all pages                                  |

Any other return type is a compile-time error listing exactly these five options.

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

    1. Only object keys of the first page
    2. Full items of the first page, with size, `ETag` and modification time

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

    1. Only object keys of the first page
    2. Full items of the first page, with size, `ETag` and modification time

!!! warning "A list operation needs a prefix source"

    Without an annotation value, without a key parameter and without a `ListObjectsArgs` parameter the
    processor fails with `S3 operation '...' has no object key`. Pass an explicit empty-prefix
    `ListObjectsArgs` if the goal is to list the whole bucket.

#### Prefix template { #prefix-template }

A prefix can also be specified as a template and method arguments can be substituted there as part of the template,
all key arguments of the method must be part of the template.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient")
    @S3.Bucket(".bucket")
    public interface SomeClient {

        @S3.List("prefix-{key1}-{key2}-") //(1)!
        ListBucketResult operation(String key1, int key2);
    }
    ```

    1. Template used to build the prefix: each template argument is substituted via `String.valueOf()`, and template arguments are specified as method argument names in `{curly braces}`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    @S3.Bucket(".bucket")
    interface SomeClient {

        @S3.List("prefix-{key1}-{key2}-") //(1)!
        fun operation(key1: String, key2: Int): ListBucketResult
    }
    ```

    1. Template used to build the prefix: each template argument is substituted via `String.valueOf()`, and template arguments are specified as method argument names in `{curly braces}`

#### List arguments { #list-args }

A `ListObjectsArgs` parameter replaces the annotation-driven prefix entirely: the object is passed to
the storage as is, so the prefix, the page size and the continuation token all come from it.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient")
    @S3.Bucket(".bucket")
    public interface SomeClient {

        @S3.List
        ListBucketResult operation(ListObjectsArgs args); //(1)!
    }
    ```

    1. When a `ListObjectsArgs` parameter is present, the annotation value and key parameters are not used to build the prefix

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    @S3.Bucket(".bucket")
    interface SomeClient {

        @S3.List
        fun operation(args: ListObjectsArgs): ListBucketResult //(1)!
    }
    ```

    1. When a `ListObjectsArgs` parameter is present, the annotation value and key parameters are not used to build the prefix

Manual pagination over `ListBucketResult`:

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

    1. Page size; the storage returns at most `1000` keys per request regardless of the value
    2. `null` when the last page has been read

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

    1. Page size; the storage returns at most `1000` keys per request regardless of the value
    2. `null` when the last page has been read

#### Separator { #separator }

A [delimiter](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-prefixes.html) groups keys
that share a prefix up to that character, which is how "directories" are emulated in S3.
It is set through `ListObjectsArgs.delimiter`, and the grouped prefixes come back in
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

    1. Group everything below `documents/` by the next `/`
    2. Pseudo-directories such as `documents/2024/`
    3. Objects that lie directly in `documents/`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val args = ListObjectsArgs()
    args.prefix = "documents/"
    args.delimiter = "/" //(1)!

    val result = client.operation(args)
    val directories = result.commonPrefixes() //(2)!
    val files = result.items() //(3)!
    ```

    1. Group everything below `documents/` by the next `/`
    2. Pseudo-directories such as `documents/2024/`
    3. Objects that lie directly in `documents/`

#### Iterators { #list-iterator }

Returning an `Iterator` hides pagination completely: the client fetches the next page only when the
current one has been consumed. This is the recommended way to walk a large bucket without holding
the whole listing in memory.

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

    1. Lazily iterates over the keys of every page
    2. Lazily iterates over the items of every page

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

    1. Lazily iterates over the keys of every page
    2. Lazily iterates over the items of every page

### Add file { #add-file }

Section describes the operation of adding an object using a declarative S3 client.
It is suggested to use the `@S3.Put` annotation for the operation.

The method must declare exactly one body parameter and return either `String` — the `ETag` reported by
the storage — or `void` / `Unit`.

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

    1. Object key by which it will be added to the storage
    2. Body of the object that will be uploaded
    3. Key can also be specified in the annotation if it is static
    4. `void` when the `ETag` is not needed

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

    1. Object key by which it will be added to the storage
    2. Body of the object that will be uploaded
    3. Key can also be specified in the annotation if it is static
    4. `Unit` when the `ETag` is not needed

Any other return type fails at compile time with
`S3 operation '@S3.Put' on method '...' has unsupported return type`, expecting `String or void`.

#### File body { #file-body }

Exactly one body parameter is required, and its type decides how the upload is performed:

| Body type                  | Kotlin type               | Upload strategy                                                                                        |
|----------------------------|---------------------------|---------------------------------------------------------------------------------------------------------|
| `byte[]`                   | `ByteArray`               | Single `PUT` of the whole array                                                                          |
| `ByteBuffer`               | `ByteBuffer`              | Single `PUT` of `remaining()` bytes; a heap buffer is used directly, a direct buffer is copied first     |
| `InputStream`              | `InputStream`             | [Multipart upload](#multipart-upload) driven by `upload.partSize`                                        |
| `S3Client.ContentWriter`   | `S3Client.ContentWriter`  | Streaming `PUT` with `aws-chunked` encoding, chunk size from `upload.chunkSize`                          |

`ContentWriter` is the way to stream a body of known length without materialising it:

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

    1. Called by the client while the request body is being written
    2. Exact content length, required to sign the request

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

    1. Called by the client while the request body is being written
    2. Exact content length, required to sign the request

!!! warning "Body type"

    A `@S3.Put` method with no body parameter fails with `has no upload body parameter`, and a method with
    more than one body parameter fails with `has N upload body parameters, but only one body parameter is supported`.
    An unsupported body type fails with `has unsupported body type`.

#### Key template { #key-template-2 }

The key can also be specified as a template and method arguments can be substituted there as part of the template,
all key arguments of the method must be part of the template.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient")
    @S3.Bucket(".bucket")
    public interface SomeClient {

        @S3.Put("prefix-{key1}-{key2}-suffix") //(1)!
        String operation(String key1, int key2, byte[] body); //(2)!
    }
    ```

    1. Template used to build the key: each template argument is substituted via `String.valueOf()`, and template arguments are specified as method argument names in `{curly braces}`
    2. The body parameter is never part of the key template

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    @S3.Bucket(".bucket")
    interface SomeClient {

        @S3.Put("prefix-{key1}-{key2}-suffix") //(1)!
        fun operation(key1: String, key2: Int, body: ByteArray): String //(2)!
    }
    ```

    1. Template used to build the key: each template argument is substituted via `String.valueOf()`, and template arguments are specified as method argument names in `{curly braces}`
    2. The body parameter is never part of the key template

#### Content type and encoding { #content-type }

`Content-Type`, `Content-Encoding` and every other upload header are set through a `PutObjectArgs`
parameter rather than through the annotation:

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

    1. `Content-Type` of the object
    2. `Content-Encoding` of the object
    3. Storage class of the object
    4. Object tags in `URL`-query format

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

    1. `Content-Type` of the object
    2. `Content-Encoding` of the object
    3. Storage class of the object
    4. Object tags in `URL`-query format

#### Multipart upload { #multipart-upload }

An `InputStream` body is uploaded as a multipart upload without any extra code. The client reads the
stream in `upload.partSize` chunks; if the whole stream fits into the first chunk it is sent as a
single `PUT` instead, and the multipart upload is never started.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient")
    @S3.Bucket(".bucket")
    public interface SomeClient {

        @S3.Put("prefix-{key}")
        String operation(String key, InputStream body); //(1)!
    }
    ```

    1. The stream is closed by the client when the upload finishes

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    @S3.Bucket(".bucket")
    interface SomeClient {

        @S3.Put("prefix-{key}")
        fun operation(key: String, body: InputStream): String //(1)!
    }
    ```

    1. The stream is closed by the client when the upload finishes

===! ":material-code-json: `Hocon`"

    ```javascript
    s3client.someClient {
        upload {
            partSize = "16MiB" //(1)!
        }
    }
    ```

    1.  Part size for `InputStream` uploads, must be between `5MiB` and `5GiB` per the `S3` specification (default: `5MiB`)

=== ":simple-yaml: `YAML`"

    ```yaml
    s3client:
      someClient:
        upload:
          partSize: "16MiB" #(1)!
    ```

    1.  Part size for `InputStream` uploads, must be between `5MiB` and `5GiB` per the `S3` specification (default: `5MiB`)

A `PutObjectArgs` parameter is honoured here as well: its values are translated into
`CreateMultipartUpload` and `CompleteMultipartUpload` arguments.

If an `IOException` occurs while reading the stream, the client rethrows it as
[`S3ClientUnknownException`](#unknown-exception).

### Delete file { #delete-file }

Section describes the operation of deleting an object using a declarative S3 client.
It is suggested to use the `@S3.Delete` annotation for the operation. The return type must be
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

    1. Object deletion operation
    2. Key of the object to delete
    3. The key of the object can be specified in the annotation
    4. Version id, `MFA` and conditional deletion parameters

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

    1. Object deletion operation
    2. Key of the object to delete
    3. The key of the object can be specified in the annotation
    4. Version id, `MFA` and conditional deletion parameters

Deleting an object that does not exist — or an object in a bucket that does not exist — is not an error:
`S3` answers such a `DELETE` with success.

!!! warning "No batch delete in the declarative client"

    `@S3.Delete` always generates a single-object `DeleteObject` request. A method such as
    `void operation(List<String> keys)` is **not** supported and fails at compile time, because a
    collection cannot be used as an object key. Batch deletion is available through the
    [imperative client](#client-imperative) — `S3Client#deleteObjects` — or through the
    [AWS SDK client](#aws).

#### Key template { #key-template-3 }

The key can also be specified as a template and method arguments can be substituted there as part of the template,
all key arguments of the method must be part of the template.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @S3.Client("s3client.someClient")
    @S3.Bucket(".bucket")
    public interface SomeClient {

        @S3.Delete("prefix-{key1}-{key2}-suffix") //(1)!
        void operation(String key1, int key2); //(2)!
    }
    ```

    1. Template used to build the key: each template argument is substituted via `String.valueOf()`, and template arguments are specified as method argument names in `{curly braces}`
    2. All key arguments of the method must be part of the key template

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @S3.Client("s3client.someClient")
    @S3.Bucket(".bucket")
    interface SomeClient {

        @S3.Delete("prefix-{key1}-{key2}-suffix") //(1)!
        fun operation(key1: String, key2: Int) //(2)!
    }
    ```

    1. Template used to build the key: each template argument is substituted via `String.valueOf()`, and template arguments are specified as method argument names in `{curly braces}`
    2. All key arguments of the method must be part of the key template

### Custom factory { #factory-tag }

Every generated client asks the graph for an `S3ClientFactory` and builds its `S3Client` through it.
The `factoryTag` attribute of `@S3.Client` makes the client request a **tagged** factory instead of the
default one, which is how a single application can run clients on different transports or with a
different telemetry setup:

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

    1. The generated module requires `@Tag(SomeClient.CustomFactory.class) S3ClientFactory`
    2. Any class works as a tag marker

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

    1. A dedicated `HTTP` client for this `S3` client only

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

    1. The generated module requires `@Tag(SomeClient.CustomFactory::class) S3ClientFactory`
    2. Any class works as a tag marker

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

    1. A dedicated `HTTP` client for this `S3` client only

Without `factoryTag`, the default `S3ClientFactory` from `KoraS3ClientModule` is used: it takes the
`HttpClient` from the graph and wires module telemetry.

### Signatures { #signatures }

Available signatures for declarative `S3` client methods out of the box:

===! ":fontawesome-brands-java: `Java`"

    The `T` refers to the type of the return value.

    - `T myMethod()`

=== ":simple-kotlin: `Kotlin`"

    By `T` we mean the type of the return value, either `T?`, or `Unit`.

    - `fun myMethod(): T`

`S3` clients are **synchronous**. There are no `CompletionStage`, `CompletableFuture`, `Mono` or `Flux`
signatures, and a `suspend` function is rejected by the symbol processor with an explicit
`Suspend methods are not supported by the S3 client generator` error. Run blocking operations in
parallel with the tools of the platform, for example on virtual threads.

## Models { #models }

All model types live in `io.koraframework.s3.client.kora.model` and its `request` / `response` subpackages.

### GetObjectResult { #model-get-object-result }

Result of a [get object](#get-file) operation. It extends `HttpClientResponse`, so it exposes the raw
`HTTP` response and must be closed:

| Method                          | Description                                                                       |
|---------------------------------|-----------------------------------------------------------------------------------|
| `int code()`                    | `HTTP` status code of the response                                                 |
| `HttpHeaders headers()`         | `HTTP` response headers                                                            |
| `HttpBodyInput body()`          | Object body, read via `asInputStream()`                                            |
| `ContentRange contentRange()`   | Parsed `Content-Range` header, only meaningful for a [ranged](#range) request      |
| `void close()`                  | Releases the response and the underlying connection                                |

`ContentRange` is a record of `firstPosition`, `lastPosition` and `completeLength`.
`contentRange()` throws `IllegalArgumentException` when the response carries no `Content-Range` header.

### HeadObjectResult { #model-head-object-result }

Result of a [metadata](#metadata) operation, a record with lazily parsed header accessors:

| Method                       | Description                                                              |
|------------------------------|--------------------------------------------------------------------------|
| `String bucket()`            | Bucket the object belongs to                                              |
| `String key()`               | Object key                                                                |
| `long size()`                | Object size in bytes                                                      |
| `HttpHeaders headers()`      | All response headers                                                      |
| `String etag()`              | `ETag` header value                                                       |
| `String versionId()`         | `x-amz-version-id` header value                                           |
| `Instant lastModified()`     | Parsed `Last-Modified` header, or `null` when the header is absent        |

### ListBucketResult { #model-list-bucket-result }

Result of a [list](#list-files) operation:

| Method                              | Description                                                                                  |
|-------------------------------------|-----------------------------------------------------------------------------------------------|
| `List<ListBucketItem> items()`      | Objects of the current page                                                                   |
| `int keyCount()`                    | Number of keys returned in this page                                                          |
| `List<String> commonPrefixes()`     | Grouped prefixes when a [delimiter](#separator) was used, otherwise `null`                     |
| `String nextContinuationToken()`    | Token for the next page, or `null` on the last page                                           |

`ListBucketResult.ListBucketItem` is a record describing one object:

| Component                    | Description                                                       |
|------------------------------|-------------------------------------------------------------------|
| `String bucket()`            | Bucket the object belongs to                                       |
| `String key()`               | Object key                                                         |
| `String etag()`              | `ETag` of the object                                               |
| `String checksumType()`      | Checksum type reported by the storage                              |
| `String checksumAlgorithm()` | Checksum algorithm reported by the storage                         |
| `Instant lastModified()`     | Last modification time                                             |
| `long size()`                | Object size in bytes                                               |
| `String storageClass()`      | Storage class, `null` when not reported                            |
| `ListBucketItemOwner owner()`| Owner (`displayName`, `id`), `null` unless `fetchOwner` was set    |

### Request arguments { #model-request-args }

Argument objects are plain mutable classes with public fields, one per S3 request parameter.
They may be passed to any matching declarative operation or to the [imperative client](#client-imperative).

| Type                | Notable fields                                                                                                                                                                                                          |
|---------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `GetObjectArgs`     | `range`, `versionId`, `partNumber`, `ifMatch`, `ifNoneMatch`, `ifModifiedSince`, `ifUnmodifiedSince`, `responseContentType`, `responseContentDisposition`, `responseContentEncoding`, `responseContentLanguage`, `responseCacheControl`, `responseExpires`, `sseCustomerAlgorithm`, `sseCustomerKey`, `checksumMode`, `requestPayer`, `expectedBucketOwner` |
| `HeadObjectArgs`    | Same set of fields as `GetObjectArgs`                                                                                                                                                                                     |
| `ListObjectsArgs`   | `prefix`, `delimiter`, `maxKeys`, `continuationToken`, `startAfter`, `fetchOwner`, `optionalObjectAttributes`, `requestPayer`, `expectedBucketOwner`                                                                       |
| `PutObjectArgs`     | `contentType`, `contentEncoding`, `contentDisposition`, `contentLanguage`, `cacheControl`, `expires`, `acl`, `storageClass`, `tagging`, `ifMatch`, `ifNoneMatch`, `serverSideEncryption`, `sseCustomerAlgorithm`, `sseCustomerKey`, `sseKmsKeyId`, `sseKmsEncryptionContext`, `bucketKeyEnabled`, `objectLockMode`, `objectLockRetainUntilDate`, `objectLockLegalHoldStatus`, `grantRead`, `grantReadAcp`, `grantWriteAcp`, `grantFullControl`, `websiteRedirectLocation`, `requestPayer`, `expectedBucketOwner` |
| `DeleteObjectArgs`  | `versionId`, `mfa`, `bypassGovernanceRetention`, `ifMatch`, `ifMatchLastModifiedTime`, `ifMatchSize`, `requestPayer`, `expectedBucketOwner`                                                                                |

The multipart types `CreateMultipartUploadArgs`, `UploadPartArgs`, `CompleteMultipartUploadArgs`,
`AbortMultipartUploadArgs`, `ListPartsArgs` and `ListMultipartUploadsArgs` follow the same shape and are
used by the [imperative client](#client-imperative).
`CreateMultipartUploadArgs.from(PutObjectArgs)` and `CompleteMultipartUploadArgs.from(PutObjectArgs)`
convert upload arguments for the multipart flow — this is what the generated client does for an
`InputStream` body.

## Imperative client { #client-imperative }

`io.koraframework.s3.client.kora.S3Client` is the low-level contract that every declarative client is
built on. It covers the whole object API plus multipart uploads, takes `credentials`, `bucket` and `key`
explicitly on every call, and is useful for operations the declarative contract does not express —
batch deletion or a manually driven multipart upload.

The module does not publish an `S3Client` component: build one from the injectable `S3ClientFactory`.

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

    1. Reads the same `S3ClientConfig` shape a declarative client would read
    2. The factory wires the `HttpClient` and telemetry from the graph

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

    1. Reads the same `S3ClientConfig` shape a declarative client would read
    2. The factory wires the `HttpClient` and telemetry from the graph

### Operations { #client-imperative-operations }

| Method                                                                     | Description                                                                                     |
|----------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------|
| `headObject(credentials, bucket, key[, args])`                             | Object metadata, throws [`S3ClientNoSuchKeyException`](#not-found-exception) when missing        |
| `headObjectOptional(credentials, bucket, key)`                             | Object metadata or `null` when missing                                                           |
| `getObject(credentials, bucket, key[, args])`                              | Object with its body, throws when missing                                                        |
| `getObjectOptional(credentials, bucket, key)`                              | Object with its body or `null` when missing                                                      |
| `putObject(credentials, bucket, key[, args], data, off, len)`              | Uploads a byte range of an array, returns the `ETag`                                             |
| `putObject(credentials, bucket, key[, args], contentWriter)`               | Streaming `aws-chunked` upload, returns the `ETag`                                               |
| `deleteObject(credentials, bucket, key[, args])`                           | Deletes one object                                                                               |
| `deleteObjects(credentials, bucket, keys)`                                 | Deletes up to `1000` objects in one request                                                      |
| `listObjectsV2(credentials, bucket, args)`                                 | One page of a listing                                                                            |
| `listObjectsV2Iterator(credentials, bucket, args)`                         | Lazy iterator that fetches pages as they are consumed                                            |
| `createMultipartUpload(credentials, bucket, key[, args])`                  | Starts a multipart upload, returns the upload id                                                 |
| `uploadPart(credentials, bucket, key, uploadId, partNumber, ...)`          | Uploads one part, returns `UploadedPart`                                                         |
| `listParts(credentials, bucket, key, uploadId, ...)`                       | Lists already uploaded parts                                                                     |
| `completeMultipartUpload(credentials, bucket, key, uploadId, parts[, args])`| Assembles the object from parts, returns the `ETag`                                              |
| `abortMultipartUpload(credentials, bucket, key, uploadId[, args])`         | Aborts a multipart upload and frees the storage of its parts                                     |
| `listMultipartUploads(credentials, bucket, args)`                          | Lists multipart uploads that were started but not completed                                      |

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

    1. Throws `S3ClientNoSuchKeyException` if the object is missing
    2. Throws [`S3ClientDeleteException`](#delete-exception) if the storage reported per-object failures

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

    1. Throws `S3ClientNoSuchKeyException` if the object is missing
    2. Throws [`S3ClientDeleteException`](#delete-exception) if the storage reported per-object failures

### Multipart upload { #client-imperative-multipart }

A multipart upload driven by hand, which is what the declarative client generates for an
`InputStream` body:

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

    1. Starts the upload and returns its identifier
    2. Part numbers start at `1`; every part but the last must be at least `5MiB`
    3. Assembles the object and returns its `ETag`
    4. Frees the storage consumed by already uploaded parts

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

    1. Starts the upload and returns its identifier
    2. Part numbers start at `1`; every part but the last must be at least `5MiB`
    3. Assembles the object and returns its `ETag`
    4. Frees the storage consumed by already uploaded parts

## Exceptions { #exceptions }

If a client operation fails, one of the `S3` exceptions from `io.koraframework.s3.client.kora.exception`
is thrown. All of them inherit from the abstract `S3ClientException`, which itself extends
`RuntimeException`, so handling is optional and unchecked.

**Exception hierarchy:**

```
RuntimeException
└── S3ClientException
    ├── S3ClientResponseException
    │   └── S3ClientErrorException
    │       └── S3ClientNoSuchKeyException
    ├── S3ClientDeleteException
    └── S3ClientUnknownException
```

**Handling example:**

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

Thrown when a requested object does not exist and the operation is not
[optional](#optional-get). Extends `S3ClientErrorException`, so `getErrorCode()` returns `NoSuchKey`.

**Recommendations:**

- Make the `@S3.Get` or `@S3.Head` result [optional](#optional-get) if absence of an object is a normal outcome
- Verify the bucket resolved by [`@S3.Bucket`](#bucket) and the requested key
- Remember that a `HEAD` request against a missing **bucket** also reports `NoSuchKey`, because the response has no body

### S3ClientDeleteException { #delete-exception }

Thrown by `S3Client#deleteObjects` when the storage reports per-object failures.
It exposes the list of individual failures:

| Method                    | Description                                                    |
|---------------------------|----------------------------------------------------------------|
| `List<Error> getErrors()` | Per-object failures, each with `key()`, `code()`, `message()`   |

**Recommendations:**

- Inspect `getErrors()` to determine which objects failed and why
- Retry the failed keys separately if the failure is transient

### S3ClientErrorException { #error-exception }

Thrown when the storage answered with an error status and a parsable `S3` error document.

| Method                     | Description                                          |
|----------------------------|------------------------------------------------------|
| `int getHttpCode()`        | `HTTP` status code of the response                    |
| `String getErrorCode()`    | Storage error code (for example, `AccessDenied`)      |
| `String getErrorMessage()` | Storage error message                                 |
| `String getRequestId()`    | Request identifier reported by the storage, may be `null` |

**Recommendations:**

- Log `getErrorCode()`, `getErrorMessage()` and `getRequestId()` for diagnostics — the request id is what storage operators need
- `SignatureDoesNotMatch` and `InvalidAccessKeyId` mean the [credentials](#credentials) or the `region` are wrong

### S3ClientResponseException { #response-exception }

Base class for every failure that carries an `HTTP` status: the storage responded, but either with an
unexpected status or with a body that is not an `S3` error document.

| Method              | Description                        |
|---------------------|------------------------------------|
| `int getHttpCode()` | `HTTP` status code of the response |

**Recommendations:**

- `403` usually means invalid credentials or a missing policy
- Enable client [logging](#configuration) and the `HTTP` client telemetry to inspect the underlying request and response

### S3ClientUnknownException { #unknown-exception }

Thrown when the operation failed before or outside the `HTTP` exchange — an `IOException` while reading
the upload stream, a transport failure, an XML parsing failure. The original failure is always the `cause`.

### S3ClientException { #base-exception }

The abstract base class of every exception above. Catch it as the last `catch` branch to handle any
storage or client error uniformly.

## AWS SDK client { #aws }

The `s3-client-aws` artifact is a thin integration around the
[AWS SDK for Java v2](https://github.com/aws/aws-sdk-java-v2). It publishes the SDK's own
`software.amazon.awssdk.services.s3.S3Client` as a graph component, configures it from the Kora
configuration and routes its `HTTP` traffic through Kora's `HttpClient` so that timeouts and telemetry
stay consistent with the rest of the application.

It contains **no `@S3` annotations and no Kora S3 models** — working with this artifact means working
with the AWS SDK API. Use it for everything the declarative contract does not cover: bucket
administration, object copying, presigned URLs, ACL and policy management, batch deletion.

### Dependency { #dependency-2 }

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "io.koraframework:s3-client-aws"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends AwsS3ClientModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("io.koraframework:s3-client-aws")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : AwsS3ClientModule
    ```

Note that the group is `io.koraframework`, not `io.koraframework.experimental` — this artifact is not
an experimental module. Requires any [HTTP client](http-client.md) module to be added: the SDK's
own `apache-client` and `netty-nio-client` transports are excluded, and Kora supplies an
`SdkHttpClient` implementation backed by the graph's `HttpClient`.

### Configuration { #configuration-2 }

Configuration is read from the `s3client.aws` path. Basic parameters:

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

    1.  `URL` of the `S3` storage (`required`, no default)
    2.  `S3` access key (`required`, no default)
    3.  `S3` secret key (`required`, no default)
    4.  `S3` storage region (default: `aws-global`)

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

    1.  `URL` of the `S3` storage (`required`, no default)
    2.  `S3` access key (`required`, no default)
    3.  `S3` secret key (`required`, no default)
    4.  `S3` storage region (default: `aws-global`)

??? note "Full Configuration"

    Complete configuration described in the `AwsS3Config` class (example values or default values are specified):

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

        1.  `URL` of the `S3` storage, passed to the SDK as an endpoint override (`required`, no default)
        2.  `S3` access key (`required`, no default)
        3.  `S3` secret key (`required`, no default)
        4.  `S3` storage region (default: `aws-global`)
        5.  Object access style, can have values `PATH` or `VIRTUAL_HOSTED` (default: `PATH`)
        6.  Maximum operation execution time, applied to the underlying `HTTP` request (default: `45s`)
        7.  When request checksums are calculated, can have values `WHEN_SUPPORTED` or `WHEN_REQUIRED` (default: `WHEN_REQUIRED`)
        8.  When response checksums are validated, can have values `WHEN_SUPPORTED` or `WHEN_REQUIRED` (default: `WHEN_REQUIRED`)
        9.  Whether to use chunked encoding when signing object data during upload (default: `true`)
        10. Enables module logging (default: `false`)
        11. Enables module metrics (default: `false`)
        12. Configures [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) for metrics (default: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
        13. Configures metric tags (default: `{}`)
        14. Enables module tracing (default: `true`)
        15. Configures tracing attributes (default: `{}`)

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

        1.  `URL` of the `S3` storage, passed to the SDK as an endpoint override (`required`, no default)
        2.  `S3` access key (`required`, no default)
        3.  `S3` secret key (`required`, no default)
        4.  `S3` storage region (default: `aws-global`)
        5.  Object access style, can have values `PATH` or `VIRTUAL_HOSTED` (default: `PATH`)
        6.  Maximum operation execution time, applied to the underlying `HTTP` request (default: `45s`)
        7.  When request checksums are calculated, can have values `WHEN_SUPPORTED` or `WHEN_REQUIRED` (default: `WHEN_REQUIRED`)
        8.  When response checksums are validated, can have values `WHEN_SUPPORTED` or `WHEN_REQUIRED` (default: `WHEN_REQUIRED`)
        9.  Whether to use chunked encoding when signing object data during upload (default: `true`)
        10. Enables module logging (default: `false`)
        11. Enables module metrics (default: `false`)
        12. Configures [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) for metrics (default: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
        13. Configures metric tags (default: `{}`)
        14. Enables module tracing (default: `true`)
        15. Configures tracing attributes (default: `{}`)

The bucket name is not part of `AwsS3Config`: the SDK takes it on every request, so declare it in your
own [`@ConfigSource`](config.md) interface.

### Usage { #aws-usage }

The SDK client is injected directly, without a tag:

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

    1. `software.amazon.awssdk.services.s3.S3Client`, the AWS SDK client
    2. Batch deletion, which the [declarative client](#delete-file) does not generate

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

    1. `software.amazon.awssdk.services.s3.S3Client`, the AWS SDK client
    2. Batch deletion, which the [declarative client](#delete-file) does not generate

Failures are reported by the SDK's own exception hierarchy — `NoSuchKeyException`,
`NoSuchBucketException`, `S3Exception` — not by the [Kora `S3` exceptions](#exceptions).

Custom SDK behaviour is added with `ExecutionInterceptor` components: every
`software.amazon.awssdk.core.interceptor.ExecutionInterceptor` published under
`@Tag(Tag.Factory.class)` is registered on the client alongside Kora's own telemetry interceptor.

## Using both artifacts { #both }

Both artifacts can live in one application: they occupy different packages and different configuration
sections, so there is nothing to reconcile.

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

    1.  Fixed path of the [AWS SDK client](#aws)
    2.  Path declared in `@S3.Client("s3client.uploads")` of the [declarative client](#client-declarative)

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

    1.  Fixed path of the [AWS SDK client](#aws)
    2.  Path declared in `@S3.Client("s3client.uploads")` of the [declarative client](#client-declarative)

### Bucket administration { #bucket-administration }

Creating a bucket or checking that it exists is not part of the `@S3` contract, so it goes through the
AWS SDK client. The bucket name from `@S3.Bucket` ends up in a generated class rather than in a
component, so the initializer reads the same configuration path itself:

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

    1. Required: nothing depends on this component, so without `@Root` it is dropped from the graph
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

    1. Required: nothing depends on this component, so without `@Root` it is dropped from the graph
    2. `software.amazon.awssdk.services.s3.S3Client`

!!! warning "A Lifecycle component nobody depends on is dropped"

    Kora builds only the part of the graph that is reachable. A component that just prepares external
    state and is not a dependency of anything is removed together with everything it pulled in,
    which surfaces as a build error such as
    `interface software.amazon.awssdk.services.s3.S3Client wasn't found in graph`.
    Mark it [`@Root`](container.md#root-component) to keep it.

## Testing { #testing }

Declarative clients can be tested with [@KoraAppTest](junit5.md) against a real `S3`-compatible storage
started in a [Testcontainers](https://java.testcontainers.org/) container — `Minio` is a convenient
choice. The storage connection parameters are supplied to the application config via system properties:

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

The application configuration used by such a test reads those system properties:

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
