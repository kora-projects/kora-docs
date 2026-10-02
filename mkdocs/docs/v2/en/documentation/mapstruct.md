---
seo_title: "MapStruct Mappers in Kora (Java)"
seo_description: "Use Java MapStruct mappers as Kora graph components: dependency setup, generated implementations, helper injection and tags."
keywords: ["Kora Framework", "Kora MapStruct", "MapStruct", "object mapping", "Java mappers"]
description: "Explains how Kora turns MapStruct @Mapper implementations into injectable graph components in Java, including annotation processors, uses, injectionStrategy, componentModel, @Tag, and generated implementations."
agent:
  use_when: "Use this file for Kora MapStruct integration in Java: @Mapper, @Mapping, mapstruct-processor, generated MapperImpl, uses, injectionStrategy, componentModel, @Tag, annotation-processors."
---

MapStruct generates Java mapper implementations at compile time. Kora makes the generated implementations ordinary components of the [dependency container](container.md). For Kotlin mapping, see [Konvert](konvert.md).

## MapStruct { #mapstruct }

### Dependency { #dependency }

The `MapStruct` extension is shipped inside the standard Kora annotation processor artifact `io.koraframework:annotation-processors`, so there is nothing extra to add on the Kora side.
The extension is registered through `ServiceLoader` and activates only when the `org.mapstruct.Mapper` annotation type is resolvable on the classpath: in a project without `MapStruct` it does nothing at all.

[Dependency](general.md#dependencies) in `build.gradle`:
```groovy
annotationProcessor "org.mapstruct:mapstruct-processor:1.6.3" //(1)!
annotationProcessor "io.koraframework:annotation-processors" //(2)!

implementation "org.mapstruct:mapstruct:1.6.3" //(3)!
```

1.  The `MapStruct` annotation processor — it is the one that generates the `<Mapper>Impl` implementation (required, no default).
2.  The Kora annotation processors, which carry the `MapStruct` extension (required, no default).
3.  The `MapStruct` annotations themselves: `@Mapper`, `@Mapping` and the rest (required, no default).

The `MapStruct` versions are yours to choose: `kora-bom` constrains only `io.koraframework:*` artifacts, so `mapstruct-processor` and `mapstruct` need an explicit version, and both should have the same one.

Both processors must be declared in the **same** `annotationProcessor` configuration so that they run in one compilation: Kora looks up the implementation that `MapStruct` produced in an earlier annotation-processing round of that same compilation.

### Usage { #usage }

Writing the mappers is entirely [MapStruct](https://mapstruct.org/)'s job; Kora only contributes the compile-time extension that publishes the generated mappers in the dependency container.

Whenever the graph needs a dependency whose type is an interface or an abstract class annotated with `@Mapper`, the extension looks up the `<Mapper>Impl` class that `MapStruct` generated in the same package and hands its single public constructor to the graph.
Because of that you do **not** annotate the mapper with [@Component](container.md#components), you do **not** import any module, and you do **not** need `componentModel = "kora"` — the default `MapStruct` component model works as is.

Declare a mapper the standard `MapStruct` way and it becomes injectable:

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

`@Mapper` is supported both on interfaces and on abstract classes, and on mappers nested inside an enclosing type — in the
nested case the extension resolves the generated implementation by joining the enclosing names with `$`
(for example `SomeInterface.CarMapper` becomes `SomeInterface$CarMapperImpl`).

#### Usage in a service { #service }

An injected mapper is an ordinary Kora component, so you constructor-inject it into a [@Component](container.md#components)
service like any other dependency:

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

### Mapper dependencies { #dependencies }

A mapper often delegates to helper mappers or services. MapStruct wires those helpers through the `uses` attribute of
`@Mapper`. To have Kora supply them from the dependency container (rather than MapStruct instantiating them itself), generate
the implementation with constructor injection: set `injectionStrategy = InjectionStrategy.CONSTRUCTOR` and
`componentModel = "jakarta"`. The generated `<Mapper>Impl` then receives every `uses` type through its public constructor, and
Kora resolves each of them from the graph — so the helper must be available as a component (for example annotated with
[@Component](container.md#components) or provided by a factory).

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

With `componentModel = "jakarta"` `MapStruct` annotates the generated implementation with `jakarta.inject` annotations, so `jakarta.inject:jakarta.inject-api` has to be on the compile classpath of the module. Kora itself neither reads nor requires those annotations — it only uses the constructor that this component model makes `MapStruct` generate.

### Tag { #tag }

A `@Mapper` may be qualified with a [@Tag](container.md#tags). Declare the same tag on the mapper and at the injection point:

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

### Errors { #errors }

The extension reports mapper problems as compilation errors of the Kora processor:

- `MapStruct mapper implementation was not generated for ...` — the graph asked for a `@Mapper` type, but the `<Mapper>Impl` class does not exist in the current compilation.
  Either the `MapStruct` processor is not declared in this module's `annotationProcessor` configuration, or `MapStruct` itself failed earlier and printed its own errors above this one. Fix the first reported error and rebuild.
- `Invalid MapStruct mapper implementation for ...` — the generated `<Mapper>Impl` has more than one public constructor, or none, so Kora cannot decide how to create it. This normally means an unexpected combination of `componentModel` and `injectionStrategy`; either adjust them, or drop the extension for this mapper and provide the implementation manually as a regular [@Component](container.md#components).
