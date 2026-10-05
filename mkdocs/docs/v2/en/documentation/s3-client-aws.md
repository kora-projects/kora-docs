---
seo_title: "Kora AWS S3 Integration: AWS SDK S3Client"
seo_description: "Configure the AWS SDK S3Client in Kora, use it with the declarative S3 client, and administer buckets."
keywords: ["Kora Framework", "AWS S3", "AWS SDK S3Client", "s3-client-aws", "object storage"]
description: "Explains the stable s3-client-aws integration, which publishes the AWS SDK S3Client in the Kora graph, configures it through s3client.aws and routes requests through Kora's HTTP client. Covers usage, configuration, combining it with the experimental declarative S3 client, and bucket administration."
agent:
  use_when: "Use this file for the stable AWS SDK S3 integration: s3-client-aws, AwsS3ClientModule, AwsS3Config, s3client.aws, software.amazon.awssdk.services.s3.S3Client, SDK operations, ExecutionInterceptor, combining both S3 artifacts, and bucket administration. For the experimental declarative Kora client, see s3-client.md."
---

The `s3-client-aws` integration is independent of the experimental [Kora S3 client](s3-client.md). Add either artifact on its own, or use both when you need generated object operations and the full AWS SDK API.

## AWS SDK client { #aws }

The `s3-client-aws` artifact is a thin integration around the
[AWS SDK for Java v2](https://github.com/aws/aws-sdk-java-v2). It publishes the SDK's own
`software.amazon.awssdk.services.s3.S3Client` as a graph component, configures it from the Kora
configuration and routes its `HTTP` traffic through Kora's `HttpClient` so that timeouts and telemetry
stay consistent with the rest of the application.

It contains **no `@S3` annotations and no Kora S3 models** — working with this artifact means working
with the AWS SDK API. Use it for everything the declarative contract does not cover: bucket
administration, object copying, presigned URLs, ACL and policy management, batch deletion.

### Dependency { #dependency }

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

### Configuration { #configuration }

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
    2. Batch deletion, which the [declarative client](s3-client.md#delete-file) does not generate

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
    2. Batch deletion, which the [declarative client](s3-client.md#delete-file) does not generate

Failures are reported by the SDK's own exception hierarchy — `NoSuchKeyException`,
`NoSuchBucketException`, `S3Exception` — not by the [Kora `S3` exceptions](s3-client.md#exceptions).

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
    2.  Path declared in `@S3.Client("s3client.uploads")` of the [declarative client](s3-client.md#client-declarative)

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
    2.  Path declared in `@S3.Client("s3client.uploads")` of the [declarative client](s3-client.md#client-declarative)

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
