---
seo_title: "Инструменты сообщества Kora: плагин IntelliJ IDEA"
seo_description: "Kora Support для IntelliJ IDEA: навигация по DI, YAML и HOCON, автодополнение путей YAML и инспекции."
keywords: ["Kora Framework", "фреймворк Kora", "плагин Kora для IntelliJ", "IntelliJ IDEA", "сообщество Kora"]
search:
  exclude: true
description: "Describes the community Kora Support plugin for IntelliJ IDEA: provider and injection-site navigation, tag and wrapper support, YAML/HOCON configuration navigation, annotation-to-config mappings, YAML path completion, and inspections."
agent:
  use_when: "Use for Kora Support capabilities, IntelliJ IDEA gutter navigation, provider lookup, YAML/HOCON config navigation, YAML path completion, and missing-provider or unknown-key inspections."
---

!!! warning "Поддержка Kora 2 в разработке"

    Плагин Kora Support пока не поддерживает Kora 2. Поддержка находится в процессе разработки.
    Ниже описаны существующие возможности плагина для Kora 1.

## Kora плагин { #kora-plugin }

[Kora Support](https://plugins.jetbrains.com/plugin/30747-kora-support) — плагин для IntelliJ IDEA, разработанный
[dsudomoin](https://github.com/dsudomoin/kora-intellij-plugin). Он помогает прослеживать внедрение зависимостей и переходить
между конфигурационными файлами и использующим их кодом. Поддерживает Java и Kotlin, включая режим K2 плагина Kotlin в IDE.

### Навигация по внедрению зависимостей { #plugin-di-navigation }

Плагин добавляет значки на полях редактора рядом с параметрами внедрения и провайдерами. Они помогают ответить на вопросы
«откуда берётся эта зависимость?» и «какие компоненты получают этот провайдер?».

| Расположение | Переход |
| --- | --- |
| Параметр конструктора класса с `@Component` | Подходящие классы-провайдеры или фабричные методы |
| Параметр фабричного метода в контексте модуля или приложения Kora | Провайдеры этого параметра |
| Объявление `@Component` или `@Repository` | Точки внедрения, использующие предоставляемый тип |
| Объявление фабричного метода | Точки внедрения, использующие его возвращаемый тип |

Например, для параметра конструктора `OrderService(OrderRepository repository)` нажмите значок на полях
рядом с `repository`, чтобы посмотреть подходящие провайдеры репозитория. Из объявления провайдера можно перейти обратно к потребителям через его значок.
Если найдено несколько целей, плагин предложит выбрать одну из них во всплывающем списке.

Поиск провайдеров учитывает фабричные методы в контекстах `@KoraApp`, `@Module`, `@KoraSubmodule` и `@Generated`,
а также унаследованные объявления модулей. При разрешении учитываются совместимость типов, аргументы обобщённых типов, `@Tag`, метааннотации с тегами
и `@Tag.Any`. Для `All<T>` и `ValueOf<T>` поиск выполняется по типу зависимости внутри обёртки.

Также распознаются отдельные провайдеры, создаваемые обработчиками аннотаций: для `ConfigValueExtractor<T>`, `JsonReader<T>` и `JsonWriter<T>`
плагин может перейти к аннотированному исходному типу без необходимости объявлять провайдер вручную.

### Навигация по конфигурации { #plugin-config-navigation }

Навигация по конфигурации работает в обе стороны:

- От метода конфигурационного интерфейса или свойства Kotlin data-класса, связанного с `@ConfigSource`, можно перейти к соответствующему ключу через значок на полях редактора.
- От ключа YAML или HOCON действие **Go to Declaration** ведёт к типу или члену конфигурации либо к аннотации, использующей этот путь.
- От строкового значения поддерживаемой аннотации действие **Go to Declaration** ведёт к записи в конфигурации.

Стандартные сочетания **Go to Declaration** — `Ctrl+B` в Windows/Linux и `Cmd+B` в macOS.
Навигация работает в файлах проекта `.yaml`, `.yml` и `.conf`. Для поддержки `.conf` включите плагин HOCON в IDE.

Например:

```java
@ConfigSource("orders")
public interface OrdersConfig {
    String endpoint();
    int batchSize();
}
```

```yaml
orders:
  endpoint: "https://orders.example.com"
  batch-size: 100
```

Значок рядом с `batchSize()` может вести к `orders.batch-size`, а **Go to Declaration** на этом ключе YAML — обратно к методу Java.
Поддерживаются вложенные типы конфигурации, имена членов в camelCase/kebab-case и типы значений map с динамическими сегментами ключей.

#### Значения аннотаций и пути конфигурации { #plugin-annotation-config }

| Значение аннотации | Путь, который ищет плагин |
| --- | --- |
| `@Retry("name")` | `resilient.retry.name` |
| `@CircuitBreaker("name")` | `resilient.circuitbreaker.name` |
| `@Timeout("name")` | `resilient.timeout.name` |
| `@Fallback("name")` | `resilient.fallback.name` |
| `@Cacheable("name")`, `@CachePut("name")`, `@CacheInvalidate("name")` | `cache.caffeine.name` и `cache.redis.name` |
| `@HttpClient(configPath = "orders")` | `httpClient.orders` |
| `@KafkaListener("messaging.orders")` | `messaging.orders`, как указано в аннотации |
| `@ScheduleAtFixedRate(config = "scheduling.cleanup")` | `scheduling.cleanup`, как указано в аннотации |
| `@ScheduleWithFixedDelay`, `@ScheduleOnce`, `@ScheduleWithCron` | Путь из атрибута `config`, как указан в аннотации |

Для навигации по расписаниям используется полное значение `config`; префикс `scheduling.` автоматически не добавляется.
При переходе из конфигурации в код можно найти потребителей аннотации и по дочернему ключу внутри указанного ею пути.

### Автодополнение YAML { #plugin-yaml-completion }

При редактировании ключа YAML вызовите **Basic Completion**. Плагин предлагает сегменты путей конфигурации из
объявлений `@ConfigSource` и зарегистрированных префиксов аннотаций, например `resilient`, `cache` и `httpClient`.
В частично написанном пути он предлагает следующий распознаваемый сегмент.

Автодополнение путей доступно для YAML; поддержка HOCON предоставляет навигацию.

### Инспекции { #plugin-inspections }

Инспекции плагина настраиваются в **Settings / Preferences → Editor → Inspections → Kora Framework**.

| Инспекция | По умолчанию | Поведение |
| --- | --- | --- |
| **Missing Kora DI provider** | Включена; слабое предупреждение | Отмечает параметр внедрения, если IDE не нашла провайдер. Для `All<T>` допускается пустая коллекция, поэтому такие параметры пропускаются. |
| **Unknown Kora config key** | Выключена; слабое предупреждение | Отмечает ключи YAML, которые не распознаны через объявления конфигурации, соответствия аннотаций или известные префиксы фреймворка. |

Инспекция неизвестных ключей пропускает известные области фреймворка, например `httpServer`, `database`, `logging` и `tracing`.
Обработчики аннотаций проверяют граф приложения при компиляции.
