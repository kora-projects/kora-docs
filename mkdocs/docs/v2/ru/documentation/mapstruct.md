---
description: "Explains how Kora turns compile-time generated mappers into graph components: MapStruct @Mapper implementations in Java and Kotlin, helper injection through uses and injectionStrategy, tags, and the Kotlin-native Konvert @Konverter KSP extension. Use when working with @Mapper, @Mapping, MapStruct, mapstruct-processor, @Konverter, Konvert, konvert-api, generated Impl, uses, injectionStrategy, componentModel, @Tag, kapt, KSP."
agent:
  use_when: "Use this file for Kora docs or implementation questions about mapping DTOs, entities and rows with MapStruct or Konvert in a Kora application, where the generated mapper implementation becomes an injectable Kora component without @Component; key triggers include @Mapper, @Mapping, MapStruct, mapstruct-processor, @Konverter, Konvert, konvert-api, generated Impl, uses, injectionStrategy, componentModel, @Tag, kapt, KSP, annotation-processors, symbol-processors."
---

Kora интегрирует библиотеки преобразования объектов так: реализация, которую такая библиотека генерирует во время компиляции, становится обычным компонентом [контейнера зависимостей](container.md).

Поддерживаются две библиотеки:

- [MapStruct](https://mapstruct.org/) — обработчик аннотаций Java, доступен из Java напрямую, а из Kotlin — через [kapt](https://kotlinlang.org/docs/kapt.html).
- [Konvert](https://github.com/mcarleio/konvert) — `KSP`-обработчик для Kotlin, работающий в той же компиляции, что и собственные `KSP`-обработчики Kora.

Обе интеграции — это расширения времени компиляции для обработчика Kora. Ни одна из них не требует отдельного артефакта Kora, модуля в `@KoraApp`, секции конфигурации или зависимости времени выполнения: вы объявляете маппер так, как это описано в документации самой библиотеки, а Kora разрешает сгенерированную реализацию в точке внедрения.

!!! tip "Какую библиотеку выбрать"

    В Java используйте `MapStruct`. В Kotlin предпочтительнее `Konvert`: `MapStruct` — это обработчик аннотаций Java, его приходится запускать через `kapt`, а это отдельный конвейер компиляции по отношению к `KSP`, в котором работают Kotlin-обработчики Kora. `Konvert` же не требует никакой дополнительной настройки сборки.

## Подключение { #dependency }

Расширение для `MapStruct` поставляется внутри стандартного артефакта обработчиков Kora — `io.koraframework:annotation-processors` для Java и `io.koraframework:symbol-processors` для Kotlin — так что со стороны Kora добавлять нечего.
Расширение регистрируется через `ServiceLoader` и активируется только тогда, когда тип аннотации `org.mapstruct.Mapper` доступен в classpath: в проекте без `MapStruct` оно не делает ничего.

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) в `build.gradle`:
    ```groovy
    annotationProcessor "org.mapstruct:mapstruct-processor:1.6.3" //(1)!
    annotationProcessor "io.koraframework:annotation-processors" //(2)!

    implementation "org.mapstruct:mapstruct:1.6.3" //(3)!
    ```

    1.  Обработчик аннотаций `MapStruct` — именно он генерирует реализацию `<Mapper>Impl` (обязательный, без значения по умолчанию).
    2.  Обработчики аннотаций Kora, в составе которых идёт расширение для `MapStruct` (обязательный, без значения по умолчанию).
    3.  Сами аннотации `MapStruct`: `@Mapper`, `@Mapping` и прочие (обязательный, без значения по умолчанию).

    Оба обработчика должны быть объявлены в **одной и той же** конфигурации `annotationProcessor`, чтобы они работали в рамках одной компиляции: Kora ищет реализацию, которую `MapStruct` создал на более раннем раунде обработки аннотаций этой же компиляции.

=== ":simple-kotlin: `Kotlin`"

    `MapStruct` — это обработчик аннотаций Java, и запустить его через `KSP` нельзя, поэтому в Kotlin он работает через [kapt](https://kotlinlang.org/docs/kapt.html), тогда как собственные обработчики Kora по-прежнему работают через [KSP](https://kotlinlang.org/docs/ksp-overview.html).
    Расширение Kora для `KSP` только ищет тип `<Mapper>Impl` — создание этого типа остаётся задачей `kapt`.

    Плагины в `build.gradle.kts`:
    ```kotlin
    plugins {
        kotlin("jvm") version ("2.4.10")
        kotlin("kapt") version ("2.4.10")
        id("com.google.devtools.ksp") version ("2.3.11")
    }
    ```

    [Зависимость](general.md#dependencies) в `build.gradle.kts`:
    ```kotlin
    kapt("org.mapstruct:mapstruct-processor:1.6.3") //(1)!
    ksp("io.koraframework:symbol-processors:2.0.0.RC1") //(2)!

    implementation("org.mapstruct:mapstruct:1.6.3") //(3)!
    ```

    1.  Обработчик аннотаций `MapStruct`, запускаемый через `kapt` (обязательный, без значения по умолчанию).
    2.  `KSP`-обработчики Kora, в составе которых идёт расширение для `MapStruct` (обязательный, без значения по умолчанию).
    3.  Сами аннотации `MapStruct`: `@Mapper`, `@Mapping` и прочие (обязательный, без значения по умолчанию).

    `KSP` должен видеть то, что сгенерировал `kapt`, и запускаться после него:
    ```kotlin
    ksp {
        allowSourcesFromOtherPlugins = true
    }
    tasks.matching { it.name.startsWith("ksp") }.configureEach {
        dependsOn(tasks.named("kaptGenerateStubsKotlin"))
        dependsOn(tasks.named("kaptKotlin"))
    }
    ```

    !!! warning "`kapt` и `KSP` в одном модуле"

        `kapt` и `KSP` — два независимых конвейера компиляции, и заставить их работать вместе в одном модуле непросто: сборка может завершаться успешно только со второй попытки, а приведённую выше настройку приходится перепроверять при каждом обновлении плагина Kotlin или `KSP`.
        Для Kotlin поддерживаемый и куда более простой вариант — [Konvert](#konvert), который является `KSP`-обработчиком и ничего из этого не требует.

## Использование { #usage }

Написание самих мапперов целиком лежит на [MapStruct](https://mapstruct.org/); Kora лишь добавляет расширение времени компиляции, которое публикует сгенерированные мапперы в контейнере зависимостей.

Когда графу требуется зависимость, тип которой — интерфейс или абстрактный класс с аннотацией `@Mapper`, расширение находит класс `<Mapper>Impl`, сгенерированный `MapStruct` в том же пакете, и передаёт графу его единственный публичный конструктор.
Поэтому маппер **не** нужно помечать аннотацией [@Component](container.md#components), **не** нужно подключать никакой модуль и **не** нужен `componentModel = "kora"` — стандартная модель компонентов `MapStruct` работает как есть.

Объявите маппер стандартным для `MapStruct` способом, и он станет доступным для внедрения:

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

При `componentModel = "jakarta"` `MapStruct` помечает сгенерированную реализацию аннотациями `jakarta.inject`, поэтому `jakarta.inject:jakarta.inject-api` должен быть в classpath компиляции модуля. Сама Kora эти аннотации не читает и не требует — она использует лишь тот конструктор, который данная модель компонентов заставляет `MapStruct` сгенерировать.

### Тег { #tag }

`@Mapper` может быть уточнён тегом [@Tag](container.md#tags). Объявите один и тот же тег на маппере и в точке внедрения — и маппер будет предоставлен именно там. Это позволяет зарегистрировать несколько мапперов одного типа и различать их:

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

### Ошибки { #errors }

Расширение сообщает о проблемах с маппером как об ошибках компиляции обработчика Kora:

- `MapStruct mapper implementation was not generated for ...` — графу потребовался тип с `@Mapper`, но класса `<Mapper>Impl` в текущей компиляции нет.
  Либо обработчик `MapStruct` не объявлен в конфигурации обработчиков этого модуля (в Kotlin — не объявлен в `kapt`, либо `KSP` запускается раньше `kapt`), либо сам `MapStruct` завершился с ошибкой раньше и вывел собственные сообщения выше этого. Исправьте первую сообщённую ошибку и пересоберите проект.
- `Generated dependency class was not found: expected type: ...` — та же ситуация со стороны Kotlin-расширения `KSP`.
- `Invalid MapStruct mapper implementation for ...` — у сгенерированного `<Mapper>Impl` больше одного публичного конструктора либо нет ни одного, и Kora не может решить, как его создавать. Обычно это означает неожиданное сочетание `componentModel` и `injectionStrategy`: либо поправьте их, либо откажитесь от расширения для этого маппера и предоставьте реализацию вручную как обычный [@Component](container.md#components).

## Konvert { #konvert }

[Konvert](https://github.com/mcarleio/konvert) генерирует мапперы для Kotlin средствами `KSP`.
Поскольку это `KSP`-обработчик, он работает в той же компиляции, что и Kotlin-обработчики Kora, поэтому проекту не нужен ни `kapt`, ни настройка задач — `Konvert` подключается просто как ещё одна зависимость `ksp(...)`.

Расширение для `Konvert` поставляется внутри `io.koraframework:symbol-processors`. Как и в случае с `MapStruct`, оно регистрируется через `ServiceLoader` и активируется только тогда, когда тип аннотации `io.mcarle.konvert.api.Konverter` доступен в classpath.

`Konvert` работает только с Kotlin — для Java используйте [MapStruct](#dependency).

### Подключение { #konvert-dependency }

[Зависимость](general.md#dependencies) в `build.gradle.kts`:
```kotlin
ksp("io.mcarle:konvert:4.5.1") //(1)!
ksp("io.koraframework:symbol-processors:2.0.0.RC1") //(2)!

implementation("io.mcarle:konvert-api:4.5.1") //(3)!
```

1.  `KSP`-обработчик `Konvert` — именно он генерирует реализации мапперов (обязательный, без значения по умолчанию).
2.  `KSP`-обработчики Kora, в составе которых идёт расширение для `Konvert` (обязательный, без значения по умолчанию).
3.  Аннотации `Konvert`, в том числе `@Konverter` (обязательный, без значения по умолчанию).

### Использование { #konvert-usage }

Пометьте интерфейс аннотацией `@Konverter` и объявите преобразования его методами:

```kotlin
data class Car(val make: String, val seatCount: Int)

data class CarDto(val make: String, val seatCount: Int)

@Konverter
interface CarMapper {

    fun carToCarDto(car: Car): CarDto
}
```

`Konvert` генерирует в том же пакете объект верхнего уровня `object CarMapperImpl : CarMapper`, а расширение Kora публикует этот объект в графе под типом `CarMapper`.
Как и в случае с `MapStruct`, маппер **не** нужно помечать аннотацией [@Component](container.md#components) и **не** нужно подключать никакой модуль.

Переименование полей, вычисляемые значения и любые другие правила по отдельным свойствам задаются собственными аннотациями `Konvert` — см. [документацию Konvert](https://github.com/mcarleio/konvert).

Внедрённый маппер — обычный компонент:

```kotlin
@Component
class CarService(private val carMapper: CarMapper) {

    fun convert(car: Car): CarDto {
        return carMapper.carToCarDto(car)
    }
}
```

### Тег { #konvert-tag }

`@Konverter` может быть уточнён тегом [@Tag](container.md#tags) точно так же, как и `@Mapper`: объявите один и тот же тег на интерфейсе маппера и в точке внедрения.

```kotlin
@Tag(MyTag::class)
@Konverter
interface CarMapper {

    fun carToCarDto(car: Car): CarDto
}

@Component
class CarService(@Tag(MyTag::class) private val carMapper: CarMapper)
```

### Ограничения { #konvert-limitations }

Расширение для `Konvert` намеренно уже, чем расширение для `MapStruct`:

- `@Konverter` распознаётся только на **интерфейсе**. Абстрактный класс с аннотацией `@Konverter` расширением не предоставляется.
- Сгенерированная реализация — это Kotlin-`object`, у него нет конструктора, и он не может получить ничего из графа. Маппер, которому нужен вспомогательный компонент, приходится писать как обычный [@Component](container.md#components), делегирующий сгенерированному объекту `CarMapperImpl`.
- Реализация ищется как `<SimpleName>Impl` в пакете самого маппера. Для `@Konverter`, вложенного в другой тип, `Konvert` всё равно генерирует объект верхнего уровня и отбрасывает имя внешнего типа — поэтому поиск отбрасывает его тоже.

### Ошибки { #konvert-errors }

- `Generated Konvert implementation was not found: expected type: ...` — графу потребовался тип с `@Konverter`, но сгенерированного объекта нет.
  Либо `KSP`-обработчик `Konvert` не объявлен в этом модуле, либо `Konvert` завершился с ошибкой раньше в той же компиляции и вывел собственные сообщения выше этого. Исправьте первую сообщённую ошибку и пересоберите проект.
