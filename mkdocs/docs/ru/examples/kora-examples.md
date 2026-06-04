---
search:
  exclude: true
description: "Explains where to start with Kora examples and guides, how to choose guided tutorials versus complete repository examples, and where to find working Java and Kotlin applications. Use when working with getting started, guides, kora-examples, templates, JUnit tests, Testcontainers, HTTP, OpenAPI, JDBC, Kafka, gRPC, S3, cache, resilience, and observability."
agent:
  use_when: "Use this file for Kora documentation navigation questions about examples, guided tutorials, repository examples, starter templates, learning paths, and choosing the right Kora sample for HTTP, OpenAPI, database, Kafka, gRPC, S3, caching, resilience, observability, or testing."
---

Первое знакомство с Kora лучше начать с руководства [Создание первого приложения на Kora](../guides/getting-started.md).
В нем пошагово собирается минимальный HTTP-сервис и объясняется, как `@KoraApp`, `@Component`, `@HttpController` и `@HttpRoute`
складываются в рабочий Gradle-проект.

Документацию удобно использовать двумя способами:

- **Руководства** - это пошаговые материалы. Они объясняют идею, форму кода и причины выбора конкретных модулей Kora.
- **Примеры из репозитория** - это готовые запускаемые сервисы. Они полезны, когда нужно сверить структуру проекта, настройки Gradle, тесты или реализацию с рабочим приложением.

## Путь по руководствам

Начните с основы:

- [Создание первого приложения на Kora](../guides/getting-started.md) - сборка и запуск минимального HTTP-сервиса.
- [Введение во внедрение зависимостей](../guides/dependency-injection-introduction.md) и [Внедрение зависимостей](../guides/dependency-injection.md) - граф зависимостей Kora, компоненты, модули, теги и фабрики.
- [Конфигурация HOCON](../guides/config-hocon.md), [Конфигурация YAML](../guides/config-yaml.md), [JSON](../guides/json.md) и [Валидация](../guides/validation.md) - базовые возможности, которые обычно нужны каждому сервису.

После этого переходите к прикладным сценариям:

- HTTP и API: [HTTP сервер](../guides/http-server.md), [HTTP сервер продвинутый](../guides/http-server-advanced.md), [HTTP клиент](../guides/http-client.md), [HTTP клиент продвинутый](../guides/http-client-advanced.md), [OpenAPI HTTP сервер](../guides/openapi-http-server.md), [OpenAPI HTTP сервер продвинутый](../guides/openapi-http-server-advanced.md) и [OpenAPI HTTP клиент](../guides/openapi-http-client.md).
- Доступ к данным: [База данных JDBC](../guides/database-jdbc.md), [База данных JDBC продвинутая](../guides/database-jdbc-advanced.md) и [База данных Cassandra](../guides/database-cassandra.md).
- Интеграции: [Kafka](../guides/messaging-kafka.md), [gRPC сервер](../guides/grpc-server.md), [gRPC сервер продвинутый](../guides/grpc-server-advanced.md), [gRPC клиент](../guides/grpc-client.md), [gRPC клиент продвинутый](../guides/grpc-client-advanced.md) и [S3](../guides/s3.md).
- Эксплуатационные возможности: [Кеширование](../guides/cache.md), [Многоуровневое кеширование](../guides/cache-multi-level.md), [Отказоустойчивость](../guides/resilient.md) и [Наблюдаемость](../guides/observability.md).
- Тестирование: [Компонентное тестирование](../guides/testing-junit.md), [Интеграционное тестирование](../guides/testing-integration.md) и [Тестирование как черный ящик](../guides/testing-black-box.md).

Многие руководства также ссылаются на готовые Java- и Kotlin-приложения в репозитории `kora-examples`, поэтому можно одновременно читать объяснение и смотреть полный проект.

## Репозиторий примеров

Большое количество готовых сервисов с различными модулями Kora находится в [репозитории kora-examples](https://github.com/kora-projects/kora-examples).

Полезные отправные точки:

- [CRUD-сервис](https://github.com/kora-projects/kora-examples/tree/master/kora-java-crud)
- [HTTP сервер](https://github.com/kora-projects/kora-examples/tree/master/kora-java-http-server)
- [HTTP клиент](https://github.com/kora-projects/kora-examples/tree/master/kora-java-http-client)
- [База данных JDBC](https://github.com/kora-projects/kora-examples/tree/master/kora-java-database-jdbc)
- [Kafka](https://github.com/kora-projects/kora-examples/tree/master/kora-java-kafka)
- [Генерация OpenAPI HTTP сервера](https://github.com/kora-projects/kora-examples/tree/master/kora-java-openapi-generator-http-server)
- [Генерация OpenAPI HTTP клиента](https://github.com/kora-projects/kora-examples/tree/master/kora-java-openapi-generator-http-client)

К каждому сервису прилагаются тесты. По ним можно посмотреть, как проверять приложение через
[JUnit 5 расширение Kora](https://github.com/kora-projects/kora-examples/blob/master/kora-java-crud/src/test/java/ru/tinkoff/kora/example/crud/ComponentTests.java)
и как запускать проверки в формате черного ящика с
[Testcontainers](https://github.com/kora-projects/kora-examples/blob/master/kora-java-crud/src/test/java/ru/tinkoff/kora/example/crud/BlackBoxTests.java).

## Шаблоны проектов

=== ":fontawesome-brands-java: `Java`"

    Новый Java-сервис можно создать на основе [Kora Java template](https://github.com/kora-projects/kora-java-template).

=== ":simple-kotlin: `Kotlin`"

    Новый Kotlin-сервис можно создать на основе [Kora Kotlin template](https://github.com/kora-projects/kora-kotlin-template).
