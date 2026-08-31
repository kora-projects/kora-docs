---
description: "Explains how Kora turns compile-time generated mappers into graph components: MapStruct @Mapper implementations in Java and Kotlin, helper injection through uses and injectionStrategy, tags, and the Kotlin-native Konvert @Konverter KSP extension. Use when working with @Mapper, @Mapping, MapStruct, mapstruct-processor, @Konverter, Konvert, konvert-api, generated Impl, uses, injectionStrategy, componentModel, @Tag, kapt, KSP."
agent:
  use_when: "Use this file for Kora docs or implementation questions about mapping DTOs, entities and rows with MapStruct or Konvert in a Kora application, where the generated mapper implementation becomes an injectable Kora component without @Component; key triggers include @Mapper, @Mapping, MapStruct, mapstruct-processor, @Konverter, Konvert, konvert-api, generated Impl, uses, injectionStrategy, componentModel, @Tag, kapt, KSP, annotation-processors, symbol-processors."
---

Kora integrates object-to-object mapping libraries by taking the implementation that such a library generates at compile time and making it an ordinary component of the [dependency container](container.md).

Two libraries are supported:

- [MapStruct](https://mapstruct.org/) — a Java annotation processor, usable from Java directly and from Kotlin through [kapt](https://kotlinlang.org/docs/kapt.html).
- [Konvert](https://github.com/mcarleio/konvert) — a `KSP` processor for Kotlin, which runs in the same compilation as Kora's own `KSP` processors.

Both integrations are compile-time extensions of the Kora processor. Neither of them requires a Kora artifact of its own, a module in `@KoraApp`, a configuration section, or a runtime dependency — you declare the mapper the way its library documents, and Kora resolves the generated implementation at the injection point.

!!! tip "Which library to pick"

    In Java use `MapStruct`. In Kotlin prefer `Konvert`: `MapStruct` is a Java annotation processor and has to be run by `kapt`, which is a separate compilation pipeline from the `KSP` one Kora's Kotlin processors run in, while `Konvert` needs no extra build wiring at all.

## Dependency { #dependency }

The `MapStruct` extension is shipped inside the standard Kora processor artifact — `io.koraframework:annotation-processors` for Java and `io.koraframework:symbol-processors` for Kotlin — so there is nothing extra to add on the Kora side.
The extension is registered through `ServiceLoader` and activates only when the `org.mapstruct.Mapper` annotation type is resolvable on the classpath: in a project without `MapStruct` it does nothing at all.

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) in `build.gradle`:
    ```groovy
    annotationProcessor "org.mapstruct:mapstruct-processor:1.6.3" //(1)!
    annotationProcessor "io.koraframework:annotation-processors" //(2)!

    implementation "org.mapstruct:mapstruct:1.6.3" //(3)!
    ```

    1.  The `MapStruct` annotation processor — it is the one that generates the `<Mapper>Impl` implementation (required, no default).
    2.  The Kora annotation processors, which carry the `MapStruct` extension (required, no default).
    3.  The `MapStruct` annotations themselves: `@Mapper`, `@Mapping` and the rest (required, no default).

    Both processors must be declared in the **same** `annotationProcessor` configuration so that they run in one compilation: Kora looks up the implementation that `MapStruct` produced in an earlier annotation-processing round of that same compilation.

=== ":simple-kotlin: `Kotlin`"

    `MapStruct` is a Java annotation processor and cannot be run by `KSP`, so in Kotlin it has to be run by [kapt](https://kotlinlang.org/docs/kapt.html), while Kora's own processors keep running under [KSP](https://kotlinlang.org/docs/ksp-overview.html).
    Kora's `KSP` extension only looks the `<Mapper>Impl` type up — producing it stays `kapt`'s job.

    Plugins in `build.gradle.kts`:
    ```kotlin
    plugins {
        kotlin("jvm") version ("2.4.10")
        kotlin("kapt") version ("2.4.10")
        id("com.google.devtools.ksp") version ("2.3.11")
    }
    ```

    [Dependency](general.md#dependencies) in `build.gradle.kts`:
    ```kotlin
    kapt("org.mapstruct:mapstruct-processor:1.6.3") //(1)!
    ksp("io.koraframework:symbol-processors:2.0.0.RC1") //(2)!

    implementation("org.mapstruct:mapstruct:1.6.3") //(3)!
    ```

    1.  The `MapStruct` annotation processor, run by `kapt` (required, no default).
    2.  The Kora `KSP` processors, which carry the `MapStruct` extension (required, no default).
    3.  The `MapStruct` annotations themselves: `@Mapper`, `@Mapping` and the rest (required, no default).

    `KSP` must be able to see what `kapt` generated, and must run after it:
    ```kotlin
    ksp {
        allowSourcesFromOtherPlugins = true
    }
    tasks.matching { it.name.startsWith("ksp") }.configureEach {
        dependsOn(tasks.named("kaptGenerateStubsKotlin"))
        dependsOn(tasks.named("kaptKotlin"))
    }
    ```

    !!! warning "`kapt` and `KSP` in one module"

        `kapt` and `KSP` are two independent compilation pipelines, and making them cooperate inside a single module is fragile: the build may only succeed on the second attempt, and the wiring above has to be re-checked whenever the Kotlin or `KSP` plugin is upgraded.
        For Kotlin the supported and much simpler option is [Konvert](#konvert), which is a `KSP` processor and therefore needs none of this.

## Usage { #usage }

Writing the mappers is entirely [MapStruct](https://mapstruct.org/)'s job; Kora only contributes the compile-time extension that publishes the generated mappers in the dependency container.

Whenever the graph needs a dependency whose type is an interface or an abstract class annotated with `@Mapper`, the extension looks up the `<Mapper>Impl` class that `MapStruct` generated in the same package and hands its single public constructor to the graph.
Because of that you do **not** annotate the mapper with [@Component](container.md#components), you do **not** import any module, and you do **not** need `componentModel = "kora"` — the default `MapStruct` component model works as is.

Declare a mapper the standard `MapStruct` way and it becomes injectable:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public enum CarType { TYPE1, TYPE2 }

    public record Car(String make, int numberOfSeats, CarType type) { }

    public record CarDto(String make, int seatCount, String type) { }

    @Mapper
    public interface CarMapper {

        @Mapping(source = "numberOfSeats", target = "seatCount")
        CarDto map(Car car);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    enum class CarType { TYPE1, TYPE2 }

    data class Car(val make: String, val numberOfSeats: Int, val type: CarType)

    data class CarDto(val make: String, val seatCount: Int, val type: String)

    @Mapper
    interface CarMapper {

        @Mapping(source = "numberOfSeats", target = "seatCount")
        fun map(car: Car): CarDto
    }
    ```

`@Mapper` is supported both on interfaces and on abstract classes, and on mappers nested inside an enclosing type — in the
nested case the extension resolves the generated implementation by joining the enclosing names with `$`
(for example `SomeInterface.CarMapper` becomes `SomeInterface$CarMapperImpl`).

### Usage in a service { #service }

An injected mapper is an ordinary Kora component, so you constructor-inject it into a [@Component](container.md#components)
service like any other dependency:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class CarService {

        private final CarMapper carMapper;

        public CarService(CarMapper carMapper) {
            this.carMapper = carMapper;
        }

        public CarDto convert(Car car) {
            return carMapper.map(car);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class CarService(private val carMapper: CarMapper) {

        fun convert(car: Car): CarDto {
            return carMapper.map(car)
        }
    }
    ```

### Mapper dependencies { #dependencies }

A mapper often delegates to helper mappers or services. MapStruct wires those helpers through the `uses` attribute of
`@Mapper`. To have Kora supply them from the dependency container (rather than MapStruct instantiating them itself), generate
the implementation with constructor injection: set `injectionStrategy = InjectionStrategy.CONSTRUCTOR` and
`componentModel = "jakarta"`. The generated `<Mapper>Impl` then receives every `uses` type through its public constructor, and
Kora resolves each of them from the graph — so the helper must be available as a component (for example annotated with
[@Component](container.md#components) or provided by a factory).

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class DateMapper {

        public String asString(Date date) {
            return date != null ? new SimpleDateFormat("yyyy-MM-dd").format(date) : null;
        }

        public Date asDate(String date) throws ParseException {
            return date != null ? new SimpleDateFormat("yyyy-MM-dd").parse(date) : null;
        }
    }

    @Mapper(uses = DateMapper.class,
            injectionStrategy = InjectionStrategy.CONSTRUCTOR,
            componentModel = "jakarta")
    public interface CarMapper {

        @Mapping(source = "numberOfSeats", target = "seatCount")
        CarDto map(Car car);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class DateMapper {

        fun asString(date: Date?): String? =
            date?.let { SimpleDateFormat("yyyy-MM-dd").format(it) }

        fun asDate(date: String?): Date? =
            date?.let { SimpleDateFormat("yyyy-MM-dd").parse(it) }
    }

    @Mapper(uses = [DateMapper::class],
            injectionStrategy = InjectionStrategy.CONSTRUCTOR,
            componentModel = "jakarta")
    interface CarMapper {

        @Mapping(source = "numberOfSeats", target = "seatCount")
        fun map(car: Car): CarDto
    }
    ```

With `componentModel = "jakarta"` `MapStruct` annotates the generated implementation with `jakarta.inject` annotations, so `jakarta.inject:jakarta.inject-api` has to be on the compile classpath of the module. Kora itself neither reads nor requires those annotations — it only uses the constructor that this component model makes `MapStruct` generate.

### Tag { #tag }

A `@Mapper` may be qualified with a [@Tag](container.md#tags). Declare the same tag on the mapper and at the injection point, and the mapper is provided exactly there. This lets you register several mappers of the same type and disambiguate them:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Tag(MyTag.class)
    @Mapper
    public interface CarMapper {

        @Mapping(source = "numberOfSeats", target = "seatCount")
        CarDto map(Car car);
    }

    @Component
    public final class CarService {

        public CarService(@Tag(MyTag.class) CarMapper carMapper) {
            // ...
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Tag(MyTag::class)
    @Mapper
    interface CarMapper {

        @Mapping(source = "numberOfSeats", target = "seatCount")
        fun map(car: Car): CarDto
    }

    @Component
    class CarService(@Tag(MyTag::class) private val carMapper: CarMapper)
    ```

### Errors { #errors }

The extension reports mapper problems as compilation errors of the Kora processor:

- `MapStruct mapper implementation was not generated for ...` — the graph asked for a `@Mapper` type, but the `<Mapper>Impl` class does not exist in the current compilation.
  Either the `MapStruct` processor is not declared in this module's processor configuration (in Kotlin — not declared in `kapt`, or `KSP` runs before `kapt`), or `MapStruct` itself failed earlier and printed its own errors above this one. Fix the first reported error and rebuild.
- `Generated dependency class was not found: expected type: ...` — the same situation as seen by the Kotlin `KSP` extension.
- `Invalid MapStruct mapper implementation for ...` — the generated `<Mapper>Impl` has more than one public constructor, or none, so Kora cannot decide how to create it. This normally means an unexpected combination of `componentModel` and `injectionStrategy`; either adjust them, or drop the extension for this mapper and provide the implementation manually as a regular [@Component](container.md#components).

## Konvert { #konvert }

[Konvert](https://github.com/mcarleio/konvert) generates Kotlin mappers with `KSP`.
Because it is a `KSP` processor it runs in the same compilation as Kora's own Kotlin processors, so a project needs neither `kapt` nor any task wiring — `Konvert` is simply another `ksp(...)` dependency.

The `Konvert` extension is shipped inside `io.koraframework:symbol-processors`. As with `MapStruct`, it is registered through `ServiceLoader` and activates only when the `io.mcarle.konvert.api.Konverter` annotation type is resolvable on the classpath.

`Konvert` is Kotlin-only — for Java use [MapStruct](#dependency).

### Dependency { #konvert-dependency }

[Dependency](general.md#dependencies) in `build.gradle.kts`:
```kotlin
ksp("io.mcarle:konvert:4.5.1") //(1)!
ksp("io.koraframework:symbol-processors:2.0.0.RC1") //(2)!

implementation("io.mcarle:konvert-api:4.5.1") //(3)!
```

1.  The `Konvert` `KSP` processor — it is the one that generates the mapper implementations (required, no default).
2.  The Kora `KSP` processors, which carry the `Konvert` extension (required, no default).
3.  The `Konvert` annotations, `@Konverter` among them (required, no default).

### Usage { #konvert-usage }

Annotate an interface with `@Konverter` and declare the conversions as its methods:

```kotlin
data class Car(val make: String, val seatCount: Int)

data class CarDto(val make: String, val seatCount: Int)

@Konverter
interface CarMapper {

    fun carToCarDto(car: Car): CarDto
}
```

`Konvert` generates a top-level `object CarMapperImpl : CarMapper` in the same package, and the Kora extension publishes that object in the graph under the `CarMapper` type.
As with `MapStruct` you do **not** annotate the mapper with [@Component](container.md#components) and you do **not** import any module.

Renaming fields, computing values and any other per-property rule are expressed with `Konvert`'s own annotations — see the [Konvert documentation](https://github.com/mcarleio/konvert).

The injected mapper is an ordinary component:

```kotlin
@Component
class CarService(private val carMapper: CarMapper) {

    fun convert(car: Car): CarDto {
        return carMapper.carToCarDto(car)
    }
}
```

### Tag { #konvert-tag }

A `@Konverter` may be qualified with a [@Tag](container.md#tags) exactly like a `@Mapper`: declare the same tag on the mapper interface and at the injection point.

```kotlin
@Tag(MyTag::class)
@Konverter
interface CarMapper {

    fun carToCarDto(car: Car): CarDto
}

@Component
class CarService(@Tag(MyTag::class) private val carMapper: CarMapper)
```

### Limitations { #konvert-limitations }

The `Konvert` extension is deliberately narrower than the `MapStruct` one:

- `@Konverter` is recognised on an **interface** only. An abstract class annotated with `@Konverter` is not provided by the extension.
- The generated implementation is a Kotlin `object`, so it has no constructor and cannot receive anything from the graph. A mapper that needs a collaborator has to be written as a regular [@Component](container.md#components) that delegates to the generated `CarMapperImpl` object.
- The implementation is looked up as `<SimpleName>Impl` in the mapper's own package. For a `@Konverter` nested inside another type `Konvert` still generates a top-level object and drops the enclosing type name, so the lookup drops it as well.

### Errors { #konvert-errors }

- `Generated Konvert implementation was not found: expected type: ...` — the graph asked for a `@Konverter` type, but the generated object does not exist.
  Either the `Konvert` `KSP` processor is not declared in this module, or `Konvert` failed earlier in the same compilation and printed its own errors above this one. Fix the first reported error and rebuild.
