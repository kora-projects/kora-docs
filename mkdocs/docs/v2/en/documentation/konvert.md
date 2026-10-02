---
seo_title: "Konvert Mappers in Kora (Kotlin)"
seo_description: "Use Kotlin Konvert mappers as Kora graph components: KSP setup, generated implementations, tags and limitations."
keywords: ["Kora Framework", "Kora Konvert", "Konvert", "object mapping", "Kotlin mappers", "KSP"]
description: "Explains how Kora turns Konvert @Konverter implementations into injectable graph components in Kotlin, including KSP setup, generated object implementations, tags, limitations, and errors."
agent:
  use_when: "Use this file for Kora Konvert integration in Kotlin: @Konverter, konvert-api, KSP, symbol-processors, generated Impl object, @Tag, limitations."
---

Konvert generates Kotlin mapper implementations with KSP. Kora makes the generated implementations ordinary components of the [dependency container](container.md). For Java mapping, see [MapStruct](mapstruct.md).

## Konvert { #konvert }

[Konvert](https://github.com/mcarleio/konvert) generates Kotlin mappers with `KSP`.
Because it is a `KSP` processor it runs in the same compilation as Kora's own Kotlin processors, so `Konvert` is simply another `ksp(...)` dependency and needs no extra build wiring.

The `Konvert` extension is shipped inside `io.koraframework:symbol-processors`. It is registered through `ServiceLoader` and activates only when the `io.mcarle.konvert.api.Konverter` annotation type is resolvable on the classpath: in a project without `Konvert` it does nothing at all.

### Dependency { #konvert-dependency }

[Dependency](general.md#dependencies) in `build.gradle.kts`:
```kotlin
ksp("io.mcarle:konvert:4.5.1") //(1)!
ksp("io.koraframework:symbol-processors:2.0.0.RC2") //(2)!

implementation("io.mcarle:konvert-api:4.5.1") //(3)!
```

1.  The `Konvert` `KSP` processor — it is the one that generates the mapper implementations (required, no default).
2.  The Kora `KSP` processors, which carry the `Konvert` extension (required, no default).
3.  The `Konvert` annotations, `@Konverter` among them (required, no default).

As with [MapStruct](mapstruct.md) in Java, the `Konvert` versions are yours to choose: `kora-bom` constrains only `io.koraframework:*` artifacts.

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
You do **not** annotate the mapper with [@Component](container.md#components) and you do **not** import any module.

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

A `@Konverter` may be qualified with a [@Tag](container.md#tags): declare the same tag on the mapper interface and at the injection point, and the mapper is provided exactly there.

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

- `@Konverter` is recognised on an **interface** only. An abstract class annotated with `@Konverter` is not provided by the extension.
- The generated implementation is a Kotlin `object`, so it has no constructor and cannot receive anything from the graph. A mapper that needs a collaborator has to be written as a regular [@Component](container.md#components) that delegates to the generated `CarMapperImpl` object.
- The implementation is looked up as `<SimpleName>Impl` in the mapper's own package. For a `@Konverter` nested inside another type `Konvert` still generates a top-level object and drops the enclosing type name, so the lookup drops it as well.

### Errors { #konvert-errors }

- `Generated Konvert implementation was not found` (followed by `expected type: <package>.<Name>Impl`) — the graph asked for a `@Konverter` type, but the generated object does not exist.
  Either the `Konvert` `KSP` processor is not declared in this module, or `Konvert` failed earlier in the same compilation and printed its own errors above this one. Fix the first reported error and rebuild.
