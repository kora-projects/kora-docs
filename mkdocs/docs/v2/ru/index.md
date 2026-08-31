---
title: Главная
search:
    exclude: true
hide:
    - navigation
    - toc
description: "Overview of the Kora framework: a compile-time Java and Kotlin framework for server-side applications with reflection-free dependency injection, generated aspects and preconfigured modules for HTTP, databases, Kafka, gRPC, cache, resilience and observability. Use when you need to understand what Kora is, which modules it ships, what JDK and build tooling it requires, and where to start reading."
agent:
  use_when: "Use this file for high-level questions about what Kora is and what it provides: the Simplicity, Performance, Efficiency and Transparency principles, the list of available modules and integrations, the JDK 25 / Gradle 9.5 / Kotlin 2.4.10 / KSP 2.3.11 requirements, the io.koraframework group and the io.koraframework:kora-bom BOM, and which guide a newcomer should read first."
template: landing.html
---

Kora - это Java фреймворк общего назначения для написания серверных Java или Kotlin приложений с упором на Простоту, Производительность, Эффективность, Прозрачность.
Kora стремится предоставить достаточно высокоуровневые и простые декларативные инструменты, тонкие и знакомые высокоуровневые абстракции для разработчиков,
которые на этапе компиляции преобразуются в производительный для железа и понятный для человека код.
Оба языка программирования поддерживаются равнозначно.

Kora полностью самобытный написанный с нуля на Java фреймворк и имеет свой контейнер зависимостей собственной разработки с инверсией управления который работает на этапе компиляции.
Фреймворк является облачно ориентированным и предлагает
множество различных модулей для быстрого создания приложений такие как [HTTP сервер](documentation/http-server.md), [Kafka](documentation/kafka.md) потребители,
абстракция над [базой данных в виде репозиториев](documentation/database-common.md), отказоустойчивость, телеметрия и многое другое.

Большое внимание в Kora также делается на:

- Телеметрии, [метрикам](documentation/metrics.md) и [трассировке](documentation/tracing.md) всех модулей по `OpenTelemetry` стандарту из коробки
- Подходу когда контракт первичен и генерации кода из [OpenAPI спецификации](documentation/openapi-codegen.md)

`Производительность` - Kora подразумевает создание сопутствующего высокопроизводительного кода на этапе компиляции,
отказ от использования Reflection API во время работы, отказ от динамических прокси, предлагает тонкие абстракции, бесплатные аспекты,
только максимально эффективные реализации модулей, все это ведет к высокой производительности приложения,
низкому времени ответа и возможности обрабатывать большое количество запросов в секунду.
Все это уже сделано в фреймворке и не требует ни каких манипуляций и конфигураций со стороны разработчика.

<figure markdown="span">
  ![Kora TechEmpower](https://raw.githubusercontent.com/kora-projects/.github/refs/heads/master/storage/images/techempower_squiry_2024_01_24.jpeg "Kora TechEmpower"){ width=600 }
  <figcaption><a href="https://www.techempower.com/benchmarks/#section=test&resultsurl=https%3A%2F%2Fstatic.squiry.xyz%2Fresults%2F20240124114707.json&hw=ph&test=fortune">Kora TechEmpower внешний замер</a></figcaption>
</figure>

`Эффективность` - Вышеописанные факторы и факт того что контейнер зависимостей создается
на этапе компиляции и инициализируется максимально параллельно, позволяют достигнуть низкого времени старта.
Эти факторы позволяют эффективно использовать практики горизонтального масштабирования
и максимально утилизировать ресурсы не только в рамках приложения, но и в рамках всего кластера.
Такая утилизация позволяет не только снизить затраты на инфраструктуру
и улучшить время обработки пользовательских запросов, но и значительно повысить запас по стабильности сервисов в случае резких пиковых нагрузок.

<figure markdown="span">
  ![Kora замер времени запуска](https://raw.githubusercontent.com/kora-projects/.github/refs/heads/master/storage/images/run_in_container_joker_2024.jpeg "Kora Startup"){ width=600 }
  <figcaption>Kora замер времени запуска PetClinic</figcaption>
</figure>

`Прозрачность` - Создание читаемого исходного кода во время компиляции,
в купе с тонкими абстракциями и бесплатными аспектами ведет к высокой читаемости кода
и понимания основных механизмов работы фреймворка со стороны разработчика если требуется.
Отсутствие эффекта черного ящика где не требуется ни магия вуду ни потрошители,
высокая читаемость, одно решение на одну проблему, знакомые высокоуровневые абстракции,
все это дает прозрачность в понимании кодовой базы со стороны всей команды разработки и позволяет легко погружать
в проект новых разработчиков, в особенности стажеров. Разработчикам дается возможность понимать и контролировать
работу с инструментом разработки, что позволяет эффективно использовать его и не тратить излишнее время на изучение/заучивание
и запоминание хитрых приемов по работе с фреймворком.
Контейнер зависимостей проверяется на этапе компиляции и имеет совместимость с [GraalVM из коробки](documentation/graalvm-native.md).

`Простота` - Прозрачность кода, которую предоставляет Kora вкупе с простыми и понятными абстракциями и подходами,
позволяет легко осваивать инструмент разработки без необходимости разработчикам заучивать годами "кишки и тонкости работы с фреймворком".
Kora стремится сделать все свои оптимизации внутри себя,
выбрать за вас самые оптимальные реализации интеграций будь то HTTP-сервер или клиент,
снять с вас как разработчика эту заботу, предоставив только производительные и эффективные решения из коробки.
Kora не предполагает сложных конструкций или абстракций,
а наоборот поощряет использовать маленькие и простые кубики абстракции для решения небольших задач.
Совокупность таких простых абстракций, позволяет решать большие сложные задачи.
Такой подход не представляет сложности в понимании если смотреть на малые абстракции по отдельности и
не создает излишнюю когнитивную нагрузку на разработчика.
Kora подразумевает ровно одно наиболее эффективное решение на одну проблему,
использует и поощряет подходы направляющие разработчика писать понятный и эффективный код.
Это дает простоту разработки и повышает эффективность работы сразу всей команды разработки
и позволяет выгружать контекст из головы разработчика в понятный код который легко писать, а впоследствии читать и поддерживать.

<figure markdown="span">
  ![Kora Simplicity](https://raw.githubusercontent.com/kora-projects/.github/refs/heads/master/storage/images/kora_test_example_joker_2024.jpeg "Kora Simplicity"){ width=600 }
  <figcaption>Kora прямой и понятный подход</figcaption>
</figure>

Kora предоставляет все необходимые для современной Java или Kotlin серверной разработки инструменты:

- Внедрение и инверсию зависимостей на этапе компиляции посредством [аннотаций](documentation/container.md)
- Достаточно высокоуровневые простые абстракции и инструменты разработки
- Прозрачное аспектно-ориентированное программирование посредством аннотаций
- Типобезопасную [конфигурацию](documentation/config.md) в формате `HOCON` или `YAML`
- Большой набор пред-сконфигурированных интеграций:
    - [HTTP сервер](documentation/http-server.md) на `Undertow` и декларативные [HTTP клиенты](documentation/http-client.md) на транспортах `JDK`, `OkHttp` или `Apache`
    - [Репозитории](documentation/database-common.md) для [JDBC](documentation/database-jdbc.md) и [Cassandra](documentation/database-cassandra.md), а также [миграции схемы](documentation/database-migration.md) через `Flyway` или `Liquibase`
    - Обмен сообщениями и удаленные вызовы: потребители и продюсеры [Kafka](documentation/kafka.md), [gRPC сервер](documentation/grpc-server.md) и [gRPC клиент](documentation/grpc-client.md), [SOAP клиент](documentation/soap-client.md), [S3 клиент](documentation/s3-client.md)
    - Читатели и писатели [Json](documentation/json.md), создаваемые на этапе компиляции, и маппинг объектов через [MapStruct](documentation/mapstruct.md) или `Konvert`
    - [Кеширование](documentation/cache.md) через `Caffeine` и `Redis`, а также [отказоустойчивость](documentation/resilient.md) с circuit breaker, retry, timeout, rate limiter и fallback
    - Интеграции [планировщика задач](documentation/scheduling.md), [валидации](documentation/validation.md) и [Camunda](documentation/camunda7-bpmn.md)
- Наблюдаемость, [трассировку](documentation/tracing.md) и [метрики](documentation/metrics.md) по стандарту `OpenTelemetry`, [логирование](documentation/logging-slf4j.md) и [пробы](documentation/probes.md) для всех модулей
- Легкое и быстрое тестирование с помощью [JUnit5](documentation/junit5.md)
- Простая документация с примерами, подкрепленная [примерами и руководствами рабочих сервисов](guides/home.md)

## Требования { #requirements }

Артефакты Kora публикуются в группе `io.koraframework` и собираются под `Java` `25`,
поэтому `JDK` `25` - минимальная версия для компиляции и запуска приложения на Kora, независимо от языка.
Приложения собираются `Gradle` `9.5+`, а для `Kotlin` проектов используются `Kotlin` `2.4.10` и `KSP` `2.3.11` -
те же версии, с которыми собирается сам фреймворк.

Версии зависимостей задаются через `BOM` `io.koraframework:kora-bom`, поэтому отдельные зависимости Kora объявляются без указания версии.
Генерация кода включается обработчиком аннотаций `io.koraframework:annotation-processors` для `Java`
и `KSP` обработчиком `io.koraframework:symbol-processors` для `Kotlin`.

Точные требования к окружению и минимальный файл сборки описаны в разделах
[Совместимость](documentation/general.md#compatibility) и [Система сборки](documentation/general.md#build-system).

## Начните с руководства { #start-with-a-guide }

Продолжите с руководства [Создание первого приложения на Kora](guides/getting-started.md), чтобы собрать минимальный HTTP-сервис и увидеть, как `@KoraApp`, `@Component`, `@HttpController` и `@HttpRoute` работают вместе в реальном проекте.
