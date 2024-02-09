Модуль позволяет интегрировать библиотеку [MapStruct](https://mapstruct.org/) для преобразования классов между собой.

## Подключение

=== ":fontawesome-brands-java: `Java`"

    Зависимость `build.gradle`:
    ```groovy
    annotationProcessor "ru.tinkoff.kora:annotation-processors"
    annotationProcessor "org.mapstruct:mapstruct-processor:1.5.5.Final"
    implementation "org.mapstruct:mapstruct:1.5.5.Final"
    ```
    
=== ":simple-kotlin: `Kotlin`"

    [MapStruct](https://mapstruct.org/) в Kotlin работает с помощью [kapt](https://kotlinlang.org/docs/kapt.html), по этому требуется также настроить плагин `build.gradle.kts`:
    ```groovy
    plugins {
        kotlin("kapt") version ("1.9.21")
    }
    ```

    Надо разрешить использовать выходные данные [kapt](https://kotlinlang.org/docs/kapt.html) как входные для [KSP](https://kotlinlang.org/docs/ksp-overview.html) `build.gradle.kts`:
    ```groovy
    ksp {
        allowSourcesFromOtherPlugins = true
    }
    ```

    Зависимость `build.gradle.kts`:
    ```groovy
    kapt("org.mapstruct:mapstruct-processor:1.5.5.Final")
    implementation("org.mapstruct:mapstruct:1.5.5.Final")
    ksp("ru.tinkoff.kora:symbol-processors")
    ```

## Использование

Создание самих преобразователей ложится на библиотеку [MapStruct](https://mapstruct.org/),
Kora в данном случае лишь предоставляет созданные библиотекой классы как зависимости в контейнер зависимостей.

=== ":fontawesome-brands-java: `Java`"

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
