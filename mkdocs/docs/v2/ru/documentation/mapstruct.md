---
seo_title: "Мапперы MapStruct в Kora (Java)"
seo_description: "Мапперы MapStruct для Java как компоненты графа Kora: подключение, сгенерированные реализации, внедрение вспомогательных мапперов и теги."
keywords: ["Kora Framework", "фреймворк Kora", "MapStruct в Kora", "MapStruct", "маппинг объектов", "мапперы Java"]
description: "Explains Kora MapStruct integration in Java: @Mapper implementations as injectable graph components, annotation processors, uses, injectionStrategy, componentModel, @Tag, and generated implementations."
agent:
  use_when: "Use this file for Kora MapStruct integration in Java: @Mapper, @Mapping, mapstruct-processor, generated MapperImpl, uses, injectionStrategy, componentModel, @Tag, annotation-processors."
---

MapStruct генерирует реализации мапперов Java во время компиляции. Kora делает сгенерированные реализации обычными компонентами [контейнера зависимостей](container.md). Для Kotlin смотрите [Konvert](konvert.md).

## MapStruct { #mapstruct }

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
