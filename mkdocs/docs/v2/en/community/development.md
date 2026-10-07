---
seo_title: "Kora Community Tools: IntelliJ IDEA Plugin"
seo_description: "Kora Support for IntelliJ IDEA: DI navigation, YAML and HOCON configuration navigation, YAML path completion, and inspections."
keywords: ["Kora Framework", "Kora IntelliJ plugin", "IntelliJ IDEA", "Kora community", "IDE support"]
search:
  exclude: true
description: "Describes the community Kora Support plugin for IntelliJ IDEA: provider and injection-site navigation, tag and wrapper support, YAML/HOCON configuration navigation, annotation-to-config mappings, YAML path completion, and inspections."
agent:
  use_when: "Use for Kora Support capabilities, IntelliJ IDEA gutter navigation, provider lookup, YAML/HOCON config navigation, YAML path completion, and missing-provider or unknown-key inspections."
---

!!! warning "Kora 2 support is in development"

    Kora Support does not support Kora 2 yet. Support is being developed.
    The guide below describes the plugin's existing capabilities for Kora 1.

## Kora plugin { #kora-plugin }

[Kora Support](https://plugins.jetbrains.com/plugin/30747-kora-support) is a community plugin for IntelliJ IDEA by
[dsudomoin](https://github.com/dsudomoin/kora-intellij-plugin). It helps trace dependency injection and move between
configuration files and the code that consumes them. It supports Java and Kotlin, including the Kotlin K2 IDE mode.

### Dependency injection navigation { #plugin-di-navigation }

The plugin adds gutter icons next to injection parameters and providers. Use these icons to answer both
“where does this dependency come from?” and “which components receive this provider?”

| Location | Navigation |
| --- | --- |
| A constructor parameter in a `@Component` class | Matching provider classes or factory methods |
| A factory method parameter in a Kora module/application context | Providers for that parameter |
| A `@Component` or `@Repository` declaration | Injection sites that consume the provided type |
| A factory method declaration | Injection sites that consume its return type |

For example, for a constructor parameter such as `OrderService(OrderRepository repository)`, click the gutter icon
beside `repository` to inspect matching repository providers. From the provider declaration, use its gutter icon to navigate back to consumers.
When several targets exist, the plugin offers a selection popup.

Provider discovery includes factory methods in `@KoraApp`, `@Module`, `@KoraSubmodule`, and `@Generated` contexts,
as well as inherited module declarations. Resolution considers assignable types, generic arguments, `@Tag`, tag meta-annotations,
and `@Tag.Any`. It unwraps `All<T>` and `ValueOf<T>` when looking for the underlying dependency.

The resolver also recognizes selected annotation-generated providers: `ConfigValueExtractor<T>`, `JsonReader<T>`, and `JsonWriter<T>`
can lead to the annotated source type rather than requiring a hand-written provider.

### Configuration navigation { #plugin-config-navigation }

Configuration support works in both directions:

- From a config interface method or Kotlin data-class property associated with `@ConfigSource`, click its gutter icon to find the corresponding key.
- From a YAML or HOCON key, use **Go to Declaration** to navigate to the config type/member or an annotation that refers to that path.
- From a supported annotation's string value, use **Go to Declaration** to locate its configuration entry.

The default **Go to Declaration** shortcuts are `Ctrl+B` on Windows/Linux and `Cmd+B` on macOS.
Navigation works in `.yaml`, `.yml`, and `.conf` project files. Enable the HOCON IDE plugin for `.conf` support.

For example:

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

The `batchSize()` gutter icon can navigate to `orders.batch-size`; **Go to Declaration** on that YAML key can return to the Java method.
The resolver handles nested config types, camelCase/kebab-case member names, and map value types with dynamic key segments.

#### Annotation values and configuration paths { #plugin-annotation-config }

| Annotation value | Configuration path searched |
| --- | --- |
| `@Retry("name")` | `resilient.retry.name` |
| `@CircuitBreaker("name")` | `resilient.circuitbreaker.name` |
| `@Timeout("name")` | `resilient.timeout.name` |
| `@Fallback("name")` | `resilient.fallback.name` |
| `@Cacheable("name")`, `@CachePut("name")`, `@CacheInvalidate("name")` | `cache.caffeine.name` and `cache.redis.name` |
| `@HttpClient(configPath = "orders")` | `httpClient.orders` |
| `@KafkaListener("messaging.orders")` | `messaging.orders`, exactly as specified |
| `@ScheduleAtFixedRate(config = "scheduling.cleanup")` | `scheduling.cleanup`, exactly as specified |
| `@ScheduleWithFixedDelay`, `@ScheduleOnce`, `@ScheduleWithCron` | The `config` attribute's path, exactly as specified |

Scheduling navigation uses the complete `config` value; it does not automatically prepend `scheduling.`.
Config-to-code navigation can also find annotation consumers when selecting a child key beneath an annotation's configured path.

### YAML completion { #plugin-yaml-completion }

Invoke **Basic Completion** while editing a YAML key. The plugin suggests configuration path segments derived from
`@ConfigSource` declarations and registered annotation prefixes, such as `resilient`, `cache`, and `httpClient`.
Under a partially written path, it suggests the next recognized segment.

Path completion is available in YAML; HOCON support provides navigation.

### Inspections { #plugin-inspections }

Configure the plugin's inspections under **Settings / Preferences → Editor → Inspections → Kora Framework**.

| Inspection | Default | Behavior |
| --- | --- | --- |
| **Missing Kora DI provider** | Enabled; weak warning | Marks an injection parameter when the IDE resolver finds no provider. Empty `All<T>` collections are allowed and skipped. |
| **Unknown Kora config key** | Disabled; weak warning | Marks YAML keys not recognized through config declarations, annotation mappings, or known framework prefixes. |

The unknown-key inspection skips known framework areas such as `httpServer`, `database`, `logging`, and `tracing`.
Annotation processors validate the application graph during compilation.
