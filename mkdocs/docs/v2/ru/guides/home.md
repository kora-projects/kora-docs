---
search:
  exclude: true
description: "Explains where to start with Kora guides and examples, how to choose between step-by-step guides and complete repository examples, and where to find working Java and Kotlin applications for HTTP, OpenAPI, JDBC, Cassandra, Kafka, gRPC, S3, cache, resilience, validation, observability and testing. Use when planning a learning path through the Kora documentation."
agent:
  use_when: "Use this file for Kora documentation navigation questions about guides, repository examples, starter templates and learning paths: which guide to read first, where the finished kora-examples applications live, and which sample covers HTTP, OpenAPI, JDBC, Cassandra, Kafka, gRPC, S3, caching, resilience, validation, observability or testing."
---

Первое знакомство с Kora лучше начать с руководства [Создание первого приложения на Kora](getting-started.md).
В нем пошагово собирается минимальный HTTP-сервис и объясняется, как `@KoraApp`, `@Component`, `@HttpController` и `@HttpRoute`
складываются в рабочий Gradle-проект.

Документацию удобно использовать двумя способами:

- **Руководства** - это пошаговые материалы. Они объясняют идею, форму кода и причины выбора конкретных модулей Kora.
- **Примеры из репозитория** - это готовые запускаемые сервисы. Они полезны, когда нужно сверить структуру проекта, настройки Gradle, тесты или реализацию с рабочим приложением.

Все руководства и примеры рассчитаны на одно и то же окружение: `JDK` `25`, `Gradle` `9.5+`, `BOM` `io.koraframework:kora-bom`,
а для `Kotlin` - `Kotlin` `2.4.10` вместе с `KSP` `2.3.11`.
Само окружение описано в разделах [Совместимость](../documentation/general.md#compatibility) и [Система сборки](../documentation/general.md#build-system).

## Путь по руководствам { #guided-learning-path }

Начните с основы:

- [Создание первого приложения на Kora](getting-started.md) - сборка и запуск минимального HTTP-сервиса.
- [Введение во внедрение зависимостей](dependency-injection-introduction.md) и [Внедрение зависимостей](dependency-injection.md) - граф зависимостей Kora, компоненты, модули, теги и фабрики.
- [Конфигурация HOCON](config-hocon.md), [Конфигурация YAML](config-yaml.md) и [JSON](json.md) - базовые возможности, которые обычно нужны каждому сервису.

После этого переходите к прикладным сценариям:

- HTTP и API: [HTTP сервер](http-server.md), [HTTP сервер продвинутый](http-server-advanced.md), [HTTP клиент](http-client.md), [HTTP клиент продвинутый](http-client-advanced.md), [OpenAPI HTTP сервер](openapi-http-server.md), [OpenAPI HTTP сервер продвинутый](openapi-http-server-advanced.md) и [OpenAPI HTTP клиент](openapi-http-client.md).
- Доступ к данным: [База данных JDBC](database-jdbc.md), [База данных JDBC продвинутая](database-jdbc-advanced.md) и [База данных Cassandra](database-cassandra.md).
- Интеграции: [Kafka](messaging-kafka.md), [gRPC сервер](grpc-server.md), [gRPC сервер продвинутый](grpc-server-advanced.md), [gRPC клиент](grpc-client.md), [gRPC клиент продвинутый](grpc-client-advanced.md) и [S3](s3.md).
- Эксплуатационные возможности: [Кеширование](cache.md), [Многоуровневое кеширование](cache-multi-level.md), [Отказоустойчивость](resilient.md) и [Валидация](validation.md).
- Наблюдаемость: [Метрики](observability-metrics.md), [Трассировка](observability-tracing.md) и [Пробы](observability-probes.md).
- Тестирование: [Компонентное тестирование](testing-junit.md), [Интеграционное тестирование](testing-integration.md) и [Тестирование как черный ящик](testing-black-box.md).

Многие руководства также ссылаются на готовые Java- и Kotlin-приложения в репозитории `kora-examples`, поэтому можно одновременно читать объяснение и смотреть полный проект.

## Репозиторий примеров { #repository-examples }

Большое количество готовых сервисов с различными модулями Kora находится в [репозитории kora-examples](https://github.com/kora-projects/kora-examples).

Полезные отправные точки:

===! ":fontawesome-brands-java: `Java`"

    - [Сервис Hello World](https://github.com/kora-projects/kora-examples/tree/master/examples/java/kora-java-helloworld)
    - [CRUD-сервис](https://github.com/kora-projects/kora-examples/tree/master/examples/java/kora-java-crud)
    - [HTTP сервер](https://github.com/kora-projects/kora-examples/tree/master/examples/java/kora-java-http-server)
    - [HTTP клиент](https://github.com/kora-projects/kora-examples/tree/master/examples/java/kora-java-http-client)
    - [База данных JDBC](https://github.com/kora-projects/kora-examples/tree/master/examples/java/kora-java-database-jdbc)
    - [Kafka](https://github.com/kora-projects/kora-examples/tree/master/examples/java/kora-java-kafka)
    - [Генерация OpenAPI HTTP сервера](https://github.com/kora-projects/kora-examples/tree/master/examples/java/kora-java-openapi-generator-http-server)
    - [Генерация OpenAPI HTTP клиента](https://github.com/kora-projects/kora-examples/tree/master/examples/java/kora-java-openapi-generator-http-client)
    - [Приложение PetClinic](https://github.com/kora-projects/kora-examples/tree/master/examples/java/kora-java-petclinic)

    К каждому сервису прилагаются тесты. По ним можно посмотреть, как проверять приложение через
    [JUnit 5 расширение Kora](https://github.com/kora-projects/kora-examples/blob/master/examples/java/kora-java-crud/src/test/java/io/koraframework/example/crud/ComponentTests.java)
    и как запускать проверки в формате черного ящика с
    [Testcontainers](https://github.com/kora-projects/kora-examples/blob/master/examples/java/kora-java-crud/src/test/java/io/koraframework/example/crud/BlackBoxTests.java).

=== ":simple-kotlin: `Kotlin`"

    - [Сервис Hello World](https://github.com/kora-projects/kora-examples/tree/master/examples/kotlin/kora-kotlin-helloworld)
    - [CRUD-сервис](https://github.com/kora-projects/kora-examples/tree/master/examples/kotlin/kora-kotlin-crud)
    - [HTTP сервер](https://github.com/kora-projects/kora-examples/tree/master/examples/kotlin/kora-kotlin-http-server)
    - [HTTP клиент](https://github.com/kora-projects/kora-examples/tree/master/examples/kotlin/kora-kotlin-http-client)
    - [База данных JDBC](https://github.com/kora-projects/kora-examples/tree/master/examples/kotlin/kora-kotlin-database-jdbc)
    - [Kafka](https://github.com/kora-projects/kora-examples/tree/master/examples/kotlin/kora-kotlin-kafka)
    - [Генерация OpenAPI HTTP сервера](https://github.com/kora-projects/kora-examples/tree/master/examples/kotlin/kora-kotlin-openapi-generator-http-server)
    - [Генерация OpenAPI HTTP клиента](https://github.com/kora-projects/kora-examples/tree/master/examples/kotlin/kora-kotlin-openapi-generator-http-client)
    - [Приложение PetClinic](https://github.com/kora-projects/kora-examples/tree/master/examples/kotlin/kora-kotlin-petclinic)

    К каждому сервису прилагаются тесты. По ним можно посмотреть, как проверять приложение через
    [JUnit 5 расширение Kora](https://github.com/kora-projects/kora-examples/blob/master/examples/kotlin/kora-kotlin-crud/src/test/kotlin/io/koraframework/kotlin/example/crud/ComponentTests.kt)
    и как запускать проверки в формате черного ящика с
    [Testcontainers](https://github.com/kora-projects/kora-examples/blob/master/examples/kotlin/kora-kotlin-crud/src/test/kotlin/io/koraframework/kotlin/example/crud/BlackBoxTests.kt).

Готовые приложения, которые собираются в самих руководствах, лежат рядом с примерами - в каталогах
[guides/java](https://github.com/kora-projects/kora-examples/tree/master/guides/java) и
[guides/kotlin](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin).

## Шаблоны проектов { #project-templates }

===! ":fontawesome-brands-java: `Java`"

    Новый Java-сервис можно создать на основе [Kora Java template](https://github.com/kora-projects/kora-java-template).

=== ":simple-kotlin: `Kotlin`"

    Новый Kotlin-сервис можно создать на основе [Kora Kotlin template](https://github.com/kora-projects/kora-kotlin-template).
