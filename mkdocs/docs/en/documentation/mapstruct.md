Module allows you to integrate the [MapStruct](https://mapstruct.org/) library to convert classes between each other.

## Dependency

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) `build.gradle`:
    ```groovy
    annotationProcessor "org.mapstruct:mapstruct-processor:1.5.5.Final"
    implementation "org.mapstruct:mapstruct:1.5.5.Final"
    ```
    
=== ":simple-kotlin: `Kotlin`"

    [MapStruct](https://mapstruct.org/) in Kotlin works with [kapt](https://kotlinlang.org/docs/kapt.html), so you are required to configure kapt plugin `build.gradle.kts`:
    ``groovy
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
        dependsOn(tasks.named("kaptKotlin").get())
        tasks.named("kaptGenerateStubsKotlin").get()
    }
    ```

    Successful building of the application may be only on second try, this is a KSP behavior.

    [Dependency](general.md#dependencies) `build.gradle.kts`: 
    ```groovy
    kapt("org.mapstruct:mapstruct-processor:1.5.5.Final")
    implementation("org.mapstruct:mapstruct:1.5.5.Final")
    ```

## Usage

The creation of the transducers themselves falls to the [MapStruct](https://mapstruct.org/) library,
Kora in this case just provides the classes created by the library as dependencies in the dependency container.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application {

        public enum CarType {TYPE1, TYPE2}

        public record Car(String make, int numberOfSeats, CarType type) { }

        public record CarTO(String make, int seatCount, String type) { }

        @Mapper
        public interface CarMapper {

            @Mapping(source = "numberOfSeats", target = "seatCount")
            CarTO map(Car car);
        }
        
        default SomeService someService(CarMapper carMapper) {
            return new SomeService(carMapper);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application {

        enum class CarType { TYPE1, TYPE2 }

        data class Car(val make: String, val numberOfSeats: Int, val type: CarType)

        data class CarTO(val make: String, val seatCount: Int, val type: String)

        @Mapper
        interface CarMapper {

            @Mapping(source = "numberOfSeats", target = "seatCount")
            fun map(car: Car): CarTO
        }

        fun someService(carMapper: CarMapper): SomeService {
            return SomeService(carMapper)
        }
    }
    ```
