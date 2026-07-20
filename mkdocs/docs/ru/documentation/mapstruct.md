---
description: "Explains Kora MapStruct integration: MapStruct-generated @Mapper implementations become injectable Kora components, dependency injection of mapper helpers via uses, tags, and the compile-time extension. Use when working with @Mapper, @Mapping, MapStruct, generated Impl, uses, injectionStrategy, componentModel, @Tag, annotation processor, KSP."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora MapStruct integration where MapStruct-generated @Mapper implementations become injectable Kora components; key triggers include @Mapper, @Mapping, MapStruct, generated Impl, uses, injectionStrategy, componentModel, @Tag, annotation processor, KSP."
---

Модуль позволяет интегрировать библиотеку [MapStruct](https://mapstruct.org/) для преобразования классов между собой.

## Подключение { #dependency }

Интеграция с Kora — это расширение времени компиляции, которое активируется автоматически, как только `mapstruct-processor`
оказывается в classpath обработчиков аннотаций — никакой дополнительный артефакт Kora или подключение модуля не требуется.

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    annotationProcessor "org.mapstruct:mapstruct-processor:1.5.5.Final"
    implementation "org.mapstruct:mapstruct:1.5.5.Final"
    ```

=== ":simple-kotlin: `Kotlin`"

    [MapStruct](https://mapstruct.org/) в Kotlin работает через [kapt](https://kotlinlang.org/docs/kapt.html), поэтому требуется настроить плагин kapt в `build.gradle.kts`:
    ```groovy
    plugins {
        kotlin("kapt") version ("1.9.10")
    }
    ```

    Последняя рабочая версия для `kapt` + `ksp` — это `1.9.10-1.0.13`, в более поздних версиях KSP совместимость между двумя инструментами нарушена на уровне Gradle-плагина.

    Необходимо разрешить использование выходных данных [kapt](https://kotlinlang.org/docs/kapt.html) в качестве входных для [KSP](https://kotlinlang.org/docs/ksp-overview.html) в `build.gradle.kts`:
    ```groovy
    ksp {
        allowSourcesFromOtherPlugins = true
    }
    tasks.withType<KspTask> {
        dependsOn(tasks.named("kaptGenerateStubsKotlin").get())
        dependsOn(tasks.named("kaptKotlin").get())
    }
    ```

    Успешная сборка приложения возможна только со второй попытки, это особенность поведения KSP.

    [Зависимость](general.md#dependencies) `build.gradle.kts`: 
    ```groovy
    kapt("org.mapstruct:mapstruct-processor:1.5.5.Final")
    implementation("org.mapstruct:mapstruct:1.5.5.Final")
    ```

## Использование { #usage }

Создание самих мапперов возлагается на библиотеку [MapStruct](https://mapstruct.org/); Kora лишь добавляет
расширение времени компиляции, которое делает сгенерированные мапперы доступными в контейнере зависимостей.

Расширение регистрируется автоматически через `ServiceLoader` и активируется, как только аннотация `org.mapstruct.Mapper`
присутствует в classpath (расширение обработчика аннотаций для Java, расширение KSP для Kotlin). Для каждого
запрошенного интерфейса или абстрактного класса `@Mapper` оно находит сгенерированную MapStruct реализацию `<Mapper>Impl` в том же пакете
и предоставляет её публичный конструктор как компонент. Благодаря этому вам **не** нужен ни модуль Kora, ни какая-либо конфигурация, и вам
**не** нужен `componentModel = "kora"` — стандартный `componentModel` работает из коробки.

Объявите маппер стандартным для MapStruct способом, и он станет доступным для внедрения:

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

`@Mapper` поддерживается как на интерфейсах, так и на абстрактных классах, а также на мапперах, вложенных внутрь внешнего типа — в
случае вложенного типа расширение определяет сгенерированную реализацию, соединяя имена внешних типов через `$`
(например, `SomeInterface.CarMapper` становится `SomeInterface$CarMapperImpl`).

### Использование в сервисе { #service }

Внедрённый маппер — это обычный компонент Kora, поэтому вы внедряете его через конструктор в сервис
[@Component](container.md#components), как и любую другую зависимость:

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

### Зависимости маппера { #dependencies }

Маппер часто делегирует работу вспомогательным мапперам или сервисам. MapStruct связывает такие вспомогательные компоненты через атрибут `uses`
аннотации `@Mapper`. Чтобы Kora предоставляла их из контейнера зависимостей (вместо того, чтобы MapStruct создавала их сам), сгенерируйте
реализацию с внедрением через конструктор: задайте `injectionStrategy = InjectionStrategy.CONSTRUCTOR` и
`componentModel = "jakarta"`. Тогда сгенерированный `<Mapper>Impl` получает каждый тип из `uses` через свой публичный конструктор, и
Kora разрешает каждый из них из графа — поэтому вспомогательный компонент должен быть доступен как компонент (например, помеченный аннотацией
[@Component](container.md#components) или предоставленный фабрикой).

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

### Тег { #tag }

`@Mapper` может быть уточнён тегом [@Tag](container.md#tags), и расширение предоставляет маппер только тогда, когда запрошенные
теги совпадают с тегами, объявленными на типе маппера. Это позволяет зарегистрировать несколько мапперов одного типа и различать их
в точке внедрения:

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
