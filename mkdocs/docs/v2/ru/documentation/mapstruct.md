---
seo_title: "Мапперы MapStruct (Java) и Konvert (Kotlin) в Kora"
seo_description: "Мапперы MapStruct для Java и Konvert для Kotlin как компоненты графа Kora: подключение, внедрение, вспомогательные мапперы, теги и сгенерированные реализации."
keywords: ["Kora Framework", "фреймворк Kora", "MapStruct в Kora", "Konvert в Kora", "MapStruct", "Konvert", "маппинг объектов", "мапперы Java", "мапперы Kotlin"]
description: "Explains how Kora turns compile-time generated mappers into graph components: MapStruct @Mapper implementations in Java (annotation-processors, helper injection through uses and injectionStrategy, tags) and Konvert @Konverter implementations in Kotlin (symbol-processors, KSP, generated object Impl, tags, limitations). Use when working with @Mapper, @Mapping, MapStruct, mapstruct-processor, @Konverter, Konvert, konvert-api, generated Impl, uses, injectionStrategy, componentModel, @Tag, KSP."
agent:
  use_when: "Use this file for Kora docs or implementation questions about mapping DTOs, entities and rows with MapStruct in Java or Konvert in Kotlin, where the generated mapper implementation becomes an injectable Kora component without @Component; key triggers include @Mapper, @Mapping, MapStruct, mapstruct-processor, @Konverter, Konvert, konvert-api, generated Impl, object CarMapperImpl, uses, injectionStrategy, componentModel, @Tag, KSP, annotation-processors, symbol-processors."
---

Kora интегрирует библиотеки преобразования объектов так: реализация, которую такая библиотека генерирует во время компиляции, становится обычным компонентом [контейнера зависимостей](container.md).

Для каждого языка поддерживается своя библиотека:

- Java — [MapStruct](https://mapstruct.org/), обработчик аннотаций Java, работающий рядом с `annotation-processors` Kora.
- Kotlin — [Konvert](https://github.com/mcarleio/konvert), `KSP`-обработчик, работающий в той же компиляции, что и `symbol-processors` Kora.

Обе интеграции — это расширения времени компиляции для обработчика Kora. Ни одна из них не требует отдельного артефакта Kora, модуля в `@KoraApp`, секции конфигурации или зависимости времени выполнения: вы объявляете маппер так, как это описано в документации самой библиотеки, а Kora разрешает сгенерированную реализацию в точке внедрения.

## Java: MapStruct { #mapstruct }

Этот раздел относится к проектам на Java. Для Kotlin используйте [Konvert](#konvert).

### Подключение { #dependency }

Расширение для `MapStruct` поставляется внутри стандартного артефакта обработчиков аннотаций Kora `io.koraframework:annotation-processors`, так что со стороны Kora добавлять нечего.
Расширение регистрируется через `ServiceLoader` и активируется только тогда, когда тип аннотации `org.mapstruct.Mapper` доступен в classpath: в проекте без `MapStruct` оно не делает ничего.

[Зависимость](general.md#dependencies) в `build.gradle`:
```groovy
annotationProcessor "org.mapstruct:mapstruct-processor:1.6.3" //(1)!
annotationProcessor "io.koraframework:annotation-processors" //(2)!

implementation "org.mapstruct:mapstruct:1.6.3" //(3)!
```

1.  Обработчик аннотаций `MapStruct` — именно он генерирует реализацию `<Mapper>Impl` (обязательный, без значения по умолчанию).
2.  Обработчики аннотаций Kora, в составе которых идёт расширение для `MapStruct` (обязательный, без значения по умолчанию).
3.  Сами аннотации `MapStruct`: `@Mapper`, `@Mapping` и прочие (обязательный, без значения по умолчанию).

Версии `MapStruct` вы выбираете сами: `kora-bom` ограничивает только артефакты `io.koraframework:*`, поэтому для `mapstruct-processor` и `mapstruct` версию нужно указать явно, и она должна быть у них одинаковой.

Оба обработчика должны быть объявлены в **одной и той же** конфигурации `annotationProcessor`, чтобы они работали в рамках одной компиляции: Kora ищет реализацию, которую `MapStruct` создал на более раннем раунде обработки аннотаций этой же компиляции.

### Использование { #usage }

Написание самих мапперов целиком лежит на [MapStruct](https://mapstruct.org/); Kora лишь добавляет расширение времени компиляции, которое публикует сгенерированные мапперы в контейнере зависимостей.

Когда графу требуется зависимость, тип которой — интерфейс или абстрактный класс с аннотацией `@Mapper`, расширение находит класс `<Mapper>Impl`, сгенерированный `MapStruct` в том же пакете, и передаёт графу его единственный публичный конструктор.
Поэтому маппер **не** нужно помечать аннотацией [@Component](container.md#components), **не** нужно подключать никакой модуль и **не** нужен `componentModel = "kora"` — стандартная модель компонентов `MapStruct` работает как есть.

Объявите маппер стандартным для `MapStruct` способом, и он станет доступным для внедрения:

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

`@Mapper` поддерживается как на интерфейсах, так и на абстрактных классах, а также на мапперах, вложенных внутрь внешнего типа — в
случае вложенного типа расширение определяет сгенерированную реализацию, соединяя имена внешних типов через `$`
(например, `SomeInterface.CarMapper` становится `SomeInterface$CarMapperImpl`).

#### Использование в сервисе { #service }

Внедрённый маппер — это обычный компонент Kora, поэтому вы внедряете его через конструктор в сервис
[@Component](container.md#components), как и любую другую зависимость:

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

### Зависимости маппера { #dependencies }

Маппер часто делегирует работу вспомогательным мапперам или сервисам. MapStruct связывает такие вспомогательные компоненты через атрибут `uses`
аннотации `@Mapper`. Чтобы Kora предоставляла их из контейнера зависимостей (вместо того, чтобы MapStruct создавала их сам), сгенерируйте
реализацию с внедрением через конструктор: задайте `injectionStrategy = InjectionStrategy.CONSTRUCTOR` и
`componentModel = "jakarta"`. Тогда сгенерированный `<Mapper>Impl` получает каждый тип из `uses` через свой публичный конструктор, и
Kora разрешает каждый из них из графа — поэтому вспомогательный компонент должен быть доступен как компонент (например, помеченный аннотацией
[@Component](container.md#components) или предоставленный фабрикой).

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

При `componentModel = "jakarta"` `MapStruct` помечает сгенерированную реализацию аннотациями `jakarta.inject`, поэтому `jakarta.inject:jakarta.inject-api` должен быть в classpath компиляции модуля. Сама Kora эти аннотации не читает и не требует — она использует лишь тот конструктор, который данная модель компонентов заставляет `MapStruct` сгенерировать.

### Тег { #tag }

`@Mapper` может быть уточнён тегом [@Tag](container.md#tags). Объявите один и тот же тег на маппере и в точке внедрения:

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

### Ошибки { #errors }

Расширение сообщает о проблемах с маппером как об ошибках компиляции обработчика Kora:

- `MapStruct mapper implementation was not generated for ...` — графу потребовался тип с `@Mapper`, но класса `<Mapper>Impl` в текущей компиляции нет.
  Либо обработчик `MapStruct` не объявлен в конфигурации `annotationProcessor` этого модуля, либо сам `MapStruct` завершился с ошибкой раньше и вывел собственные сообщения выше этого. Исправьте первую сообщённую ошибку и пересоберите проект.
- `Invalid MapStruct mapper implementation for ...` — у сгенерированного `<Mapper>Impl` больше одного публичного конструктора либо нет ни одного, и Kora не может решить, как его создавать. Обычно это означает неожиданное сочетание `componentModel` и `injectionStrategy`: либо поправьте их, либо откажитесь от расширения для этого маппера и предоставьте реализацию вручную как обычный [@Component](container.md#components).

## Kotlin: Konvert { #konvert }

Этот раздел относится к проектам на Kotlin. Для Java используйте [MapStruct](#mapstruct).

[Konvert](https://github.com/mcarleio/konvert) генерирует мапперы для Kotlin средствами `KSP`.
Поскольку это `KSP`-обработчик, он работает в той же компиляции, что и Kotlin-обработчики Kora, поэтому `Konvert` подключается просто как ещё одна зависимость `ksp(...)` и не требует дополнительной настройки сборки.

Расширение для `Konvert` поставляется внутри `io.koraframework:symbol-processors`. Оно регистрируется через `ServiceLoader` и активируется только тогда, когда тип аннотации `io.mcarle.konvert.api.Konverter` доступен в classpath: в проекте без `Konvert` оно не делает ничего.

### Подключение { #konvert-dependency }

[Зависимость](general.md#dependencies) в `build.gradle.kts`:
```kotlin
ksp("io.mcarle:konvert:4.5.1") //(1)!
ksp("io.koraframework:symbol-processors:2.0.0.RC2") //(2)!

implementation("io.mcarle:konvert-api:4.5.1") //(3)!
```

1.  `KSP`-обработчик `Konvert` — именно он генерирует реализации мапперов (обязательный, без значения по умолчанию).
2.  `KSP`-обработчики Kora, в составе которых идёт расширение для `Konvert` (обязательный, без значения по умолчанию).
3.  Аннотации `Konvert`, в том числе `@Konverter` (обязательный, без значения по умолчанию).

Как и в случае с `MapStruct` в Java, версии `Konvert` вы выбираете сами: `kora-bom` ограничивает только артефакты `io.koraframework:*`.

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
Маппер **не** нужно помечать аннотацией [@Component](container.md#components) и **не** нужно подключать никакой модуль.

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

`@Konverter` может быть уточнён тегом [@Tag](container.md#tags): объявите один и тот же тег на интерфейсе маппера и в точке внедрения — и маппер будет предоставлен именно там.

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

- `@Konverter` распознаётся только на **интерфейсе**. Абстрактный класс с аннотацией `@Konverter` расширением не предоставляется.
- Сгенерированная реализация — это Kotlin-`object`, у него нет конструктора, и он не может получить ничего из графа. Маппер, которому нужен вспомогательный компонент, приходится писать как обычный [@Component](container.md#components), делегирующий сгенерированному объекту `CarMapperImpl`.
- Реализация ищется как `<SimpleName>Impl` в пакете самого маппера. Для `@Konverter`, вложенного в другой тип, `Konvert` всё равно генерирует объект верхнего уровня и отбрасывает имя внешнего типа — поэтому поиск отбрасывает его тоже.

### Ошибки { #konvert-errors }

- `Generated Konvert implementation was not found` (далее следует `expected type: <package>.<Name>Impl`) — графу потребовался тип с `@Konverter`, но сгенерированного объекта нет.
  Либо `KSP`-обработчик `Konvert` не объявлен в этом модуле, либо `Konvert` завершился с ошибкой раньше в той же компиляции и вывел собственные сообщения выше этого. Исправьте первую сообщённую ошибку и пересоберите проект.
