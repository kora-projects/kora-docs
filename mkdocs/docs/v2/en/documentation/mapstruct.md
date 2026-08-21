---
description: "Explains Kora MapStruct integration: MapStruct-generated @Mapper implementations become injectable Kora components, dependency injection of mapper helpers via uses, tags, and the compile-time extension. Use when working with @Mapper, @Mapping, MapStruct, generated Impl, uses, injectionStrategy, componentModel, @Tag, annotation processor, KSP."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora MapStruct integration where MapStruct-generated @Mapper implementations become injectable Kora components; key triggers include @Mapper, @Mapping, MapStruct, generated Impl, uses, injectionStrategy, componentModel, @Tag, annotation processor, KSP."
---

Module allows you to integrate the [MapStruct](https://mapstruct.org/) library to convert classes between each other.

## Dependency { #dependency }

The Kora integration is a compile-time extension that is auto-activated as soon as the `mapstruct-processor` is on the
annotation-processor classpath — no extra Kora artifact or module import is required.

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) `build.gradle`:
    ```groovy
    annotationProcessor "org.mapstruct:mapstruct-processor:1.5.5.Final"
    implementation "org.mapstruct:mapstruct:1.5.5.Final"
    ```

=== ":simple-kotlin: `Kotlin`"

    [MapStruct](https://mapstruct.org/) in Kotlin works with [kapt](https://kotlinlang.org/docs/kapt.html), so you are required to configure kapt plugin `build.gradle.kts`:
    ```groovy
    plugins {
        kotlin("kapt") version ("1.9.10")
    }
    ```

    The latest working version for `kapt` + `ksp` is `1.9.10-1.0.13`, in later versions of KSP the compatibility between the two tools is broken at the Gradle Plugin level.

    You need to allow the output of [kapt](https://kotlinlang.org/docs/kapt.html) to be used as input for [KSP](https://kotlinlang.org/docs/ksp-overview.html) `build.gradle.kts`:
    ```groovy
    ksp {
        allowSourcesFromOtherPlugins = true
    }
    tasks.withType<KspTask> {
        dependsOn(tasks.named("kaptGenerateStubsKotlin").get())
        dependsOn(tasks.named("kaptKotlin").get())
    }
    ```

    Successful building of the application may be only on second try, this is a KSP behavior.

    [Dependency](general.md#dependencies) `build.gradle.kts`: 
    ```groovy
    kapt("org.mapstruct:mapstruct-processor:1.5.5.Final")
    implementation("org.mapstruct:mapstruct:1.5.5.Final")
    ```

## Usage { #usage }

The creation of the mappers themselves falls to the [MapStruct](https://mapstruct.org/) library; Kora only contributes a
compile-time extension that makes the generated mappers available in the dependency container.

The extension is registered automatically through `ServiceLoader` and activates as soon as the `org.mapstruct.Mapper`
annotation is present on the classpath (an annotation-processor extension for Java, a KSP extension for Kotlin). For every
requested `@Mapper` interface or abstract class it locates the MapStruct-generated `<Mapper>Impl` in the same package and
exposes its public constructor as a component. Because of this you do **not** need any Kora module or configuration, and you
do **not** need `componentModel = "kora"` — the default `componentModel` works out of the box.

Declare a mapper the standard MapStruct way and it becomes injectable:

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

### Tag { #tag }

A `@Mapper` may be qualified with a [@Tag](container.md#tags), and the extension provides the mapper only when the requested
tags equal the tags declared on the mapper type. This lets you register several mappers of the same type and disambiguate them
at the injection point:

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
