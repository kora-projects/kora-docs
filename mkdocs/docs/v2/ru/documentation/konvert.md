---
seo_title: "Мапперы Konvert в Kora (Kotlin)"
seo_description: "Мапперы Konvert для Kotlin как компоненты графа Kora: подключение KSP, сгенерированные реализации, теги и ограничения."
keywords: ["Kora Framework", "фреймворк Kora", "Konvert в Kora", "Konvert", "маппинг объектов", "мапперы Kotlin", "KSP"]
description: "Explains Kora Konvert integration in Kotlin: @Konverter implementations as injectable graph components, KSP setup, generated object implementations, tags, limitations, and errors."
agent:
  use_when: "Use this file for Kora Konvert integration in Kotlin: @Konverter, konvert-api, KSP, symbol-processors, generated Impl object, @Tag, limitations."
---

Konvert генерирует реализации мапперов Kotlin с помощью KSP. Kora делает сгенерированные реализации обычными компонентами [контейнера зависимостей](container.md). Для Java смотрите [MapStruct](mapstruct.md).

## Konvert { #konvert }

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
