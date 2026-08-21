---
search:
  exclude: true
title: Стратегии кэширования с Kora
summary: Learn how to extend the HTTP Server guide with typed Caffeine caching, cache annotations, and local performance optimization
tags: caching, performance, caffeine, cacheable, cache-invalidate, optimization
---

# Стратегии кэширования с Kora { #caching-strategies-kora }

В этом руководстве рассматривается локальное кэширование с Kora и Caffeine. Вы узнаете, как интерфейсы кэша описывают сохраненные значения, как аннотации кэша оборачивают методы сервисов и как
инвалидация сохраняет чтения согласованными с операциями создания, обновления и удаления. Вы также увидите, как локальный кэш в памяти ускоряет повторные чтения, пока репозиторий остается источником
истины.

===! ":fontawesome-brands-java: `Java`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Java Cache App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-cache-app).

=== ":simple-kotlin: `Kotlin`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Kotlin Cache App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-cache-app).

## Что вы создадите { #youll-build }

В этом руководстве вы превратите `UserService` из руководства по HTTP-серверу в сервис, который учитывает кэш:

- прогревает кэш сразу после `createUser()`
- повторно использует кэшированные значения для повторных вызовов `getUser()`
- обновляет кэшированные значения при `updateUser()`
- удаляет устаревшие записи при `deleteUser()`
- сохраняет тот же HTTP-контракт `/users`, но делает повторные чтения дешевле

## Что вам понадобится { #youll-need }

- JDK 17 или новее
- Gradle 7+
- текстовый редактор или среда разработки
- пройденное руководство [HTTP-сервер](http-server.md)

## Требования { #prerequisites }

!!! note "Обязательно: пройдите руководство по HTTP-серверу"

    Это руководство предполагает, что вы уже прошли **[HTTP-сервер](http-server.md)** и у вас есть тот же `UserController`, `UserService`, DTO и `UserRepository` в памяти из этого руководства.

    Если вы еще не прошли руководство по HTTP-серверу, сначала сделайте это, потому что здесь сохраняется контракт API `/users` и к существующему сервисному слою добавляется кэширование.

## Обзор { #overview }

Если вы никогда раньше не работали с кэшами, основная идея проста: кэш хранит уже вычисленные или уже загруженные данные в более быстром слое хранения, чтобы приложению не приходилось повторять одну и
ту же дорогую работу при каждом запросе.

Без кэширования обычный процесс чтения выглядит так:

1. Приходит HTTP-запрос.
2. Сервис запрашивает данные у репозитория или внешней системы.
3. Репозиторий снова выполняет работу.
4. Сервис возвращает результат.

С кэшированием процесс становится таким:

1. Приходит HTTP-запрос.
2. Сервис сначала проверяет, есть ли значение в кэше.
3. Если значение закэшировано, приложение сразу возвращает его.
4. Если значения в кэше нет, приложение загружает данные из исходного источника, возвращает их и сохраняет в кэше для следующего вызова.

Это важно, потому что исходный источник часто намного медленнее или намного дороже памяти:

- обращение к базе данных требует времени на сеть, пул соединений, запрос и сопоставление
- внешний HTTP-вызов добавляет сетевую задержку и риск нижележащего сервиса
- тяжелое вычисление каждый раз тратит процессорное время
- повторное чтение под нагрузкой усиливает все перечисленное

Поэтому основные причины использовать кэш такие:

- уменьшить задержку повторных чтений
- снизить нагрузку на базы данных и нижележащие сервисы
- повысить пропускную способность при большом трафике
- сделать горячие пути более предсказуемыми

В то же время кэширование — это компромисс, а не бесплатная магия. Кэшированные данные могут устаревать, память конечна, а инвалидацию кэша нужно проектировать аккуратно. Поэтому хорошее кэширование
начинается с понимания **какие данные меняются**, **как часто они меняются** и **насколько вредны устаревшие данные**.

### Когда кэширование помогает больше всего { #caching-helps-most }

Кэширование наиболее полезно, когда верны все или большая часть этих условий:

- одни и те же ключи запрашиваются повторно
- источник истины заметно медленнее памяти
- данные меняются реже, чем читаются
- кратковременная устарелость допустима или инвалидацию легко смоделировать

Типичные примеры:

- профили пользователей
- флаги возможностей и справочные данные
- метаданные продуктов
- снимки конфигурации
- дорогие агрегированные результаты

Кэширование обычно плохо подходит, когда:

- значения меняются почти при каждом чтении
- каждый запрос использует уникальный ключ только один раз
- для каждого чтения требуется строгая согласованность в реальном времени
- правила инвалидации неизвестны или крайне сложны

### Локальный кэш и распределенный кэш { #local-distributed-cache }

В этом руководстве мы используем **Caffeine**, то есть **локальный кэш в памяти**. Это значит, что кэш живет внутри одного процесса приложения.

У этого есть важные последствия:

- он чрезвычайно быстрый, потому что это просто локальная память
- он не требует дополнительной инфраструктуры, например Redis
- он изолирован для каждого процесса, поэтому у каждого экземпляра приложения свое содержимое кэша

В среде с N экземплярами, например Kubernetes, каждый экземпляр приложения прогревает и хранит свой кэш независимо.

Это часто совершенно нормально, когда:

- прогрев кэша дешевый
- итоговая согласованность между экземплярами допустима
- вы в основном хотите уменьшить повторную работу внутри каждого экземпляра

Но это также означает:

- записи кэша не разделяются между экземплярами
- обновление или удаление значения в одном экземпляре не обновляет напрямую локальный кэш другого экземпляра
- перезапущенный экземпляр начинает с пустым кэшем

Поэтому локальные кэши Caffeine лучше воспринимать как **ускорение каждого отдельного экземпляра**, а не как глобально общий источник истины.

Если позже вам понадобится общее состояние кэша между экземплярами, это руководство естественно ведет к многоуровневой или распределенной настройке кэша.

### Почему модель кэша Kora полезна { #koras-cache-model-useful }

Kora поддерживает кэширование двумя взаимодополняющими способами:

- **Декларативное кэширование** с `@Cacheable`, `@CachePut` и `@CacheInvalidate`
- **Императивное кэширование** через внедрение контракта кэша и прямой вызов `get()`, `put()`, `invalidate()` или `invalidateAll()`

Такое сочетание полезно, потому что разным методам сервиса нужен разный уровень управления.

В этом руководстве:

- `getUser()` — классический случай чтения через кэш, поэтому `@Cacheable` подходит идеально
- `updateUser()` — естественный случай обновления значения, поэтому `@CachePut` хорошо подходит
- `deleteUser()` — очевидный случай удаления из кэша, поэтому `@CacheInvalidate` работает хорошо
- `createUser()` требует ручного прогрева кэша, потому что ключ кэша становится известен только после того, как репозиторий сгенерирует идентификатор

### Почему контракт кэша типизирован { #cache-contract-typed }

Кэши Kora — это не безымянные карты, спрятанные где-то внутри фреймворка. Вы определяете **типизированный контракт кэша**, например `CaffeineCache<String, UserResponse>`.

Это дает несколько преимуществ:

- тип ключа явный
- тип кэшированного значения явный
- компилятор помогает защитить контракт
- кэш можно внедрять как любой другой компонент
- один и тот же кэш можно использовать и аннотациями, и прямыми императивными вызовами

Поскольку `UserCaffeineCache` расширяет `CaffeineCache<String, UserResponse>`, он ведет себя как обычная зависимость, которую можно внедрять в сервисы и тесты.

Это значит, что кэш можно использовать напрямую для операций вроде:

- `get(key)`, чтобы посмотреть текущее кэшированное значение
- `put(key, value)`, чтобы вручную прогреть или перезаписать запись
- `invalidate(key)`, чтобы удалить один ключ
- `invalidateAll()`, чтобы очистить весь кэш

Так кэш остается одновременно удобным для декларативного подхода и операционно явным. Вы сохраняете поддержку фреймворка, но не теряете управление.

## Зависимости { #dependencies }

Добавьте зависимость Caffeine времени выполнения в приложение из руководства по HTTP-серверу.

===! ":fontawesome-brands-java: `Gradle Groovy`"

    Обновите `guides/guide-cache-app/build.gradle`:

    ```groovy
    dependencies {
        implementation "ru.tinkoff.kora:cache-caffeine"
    }
    ```

=== ":simple-kotlin: `Gradle Kotlin DSL`"

    Обновите `build.gradle.kts`:

    ```kotlin
    dependencies {
        implementation("ru.tinkoff.kora:cache-caffeine")
    }
    ```

## Модули { #modules }

Приложение из руководства по HTTP-серверу уже использует `HoconConfigModule`, `JsonModule` и `UndertowHttpServerModule`. Здесь мы добавляем `CaffeineCacheModule`, чтобы Kora могла сгенерировать
реализацию кэша.

===! ":fontawesome-brands-java: `Java`"

    Обновите `guides/guide-cache-app/src/main/java/ru/tinkoff/kora/guide/cache/Application.java`:

    ```java
    package ru.tinkoff.kora.guide.cache;

    import ru.tinkoff.kora.application.graph.KoraApplication;
    import ru.tinkoff.kora.cache.caffeine.CaffeineCacheModule;
    import ru.tinkoff.kora.common.KoraApp;
    import ru.tinkoff.kora.config.hocon.HoconConfigModule;
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule;
    import ru.tinkoff.kora.json.module.JsonModule;
    import ru.tinkoff.kora.logging.logback.LogbackModule;

    @KoraApp
    public interface Application extends
            HoconConfigModule,
            JsonModule,
            LogbackModule,
            UndertowHttpServerModule,
            CaffeineCacheModule {  // <----- Подключили модуль

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Обновите `src/main/kotlin/ru/tinkoff/kora/guide/cache/Application.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.cache

    import ru.tinkoff.kora.application.graph.KoraApplication
    import ru.tinkoff.kora.cache.caffeine.CaffeineCacheModule
    import ru.tinkoff.kora.common.KoraApp
    import ru.tinkoff.kora.config.hocon.HoconConfigModule
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule
    import ru.tinkoff.kora.json.module.JsonModule
    import ru.tinkoff.kora.logging.logback.LogbackModule

    @KoraApp
    interface Application :
        HoconConfigModule,
        JsonModule,
        LogbackModule,
        UndertowHttpServerModule,
        CaffeineCacheModule  // <----- Подключили модуль

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

## Реализация кеша { #cache-impl }

Кэш Kora начинается с типизированного интерфейса `@Cache`. Kora генерирует его реализацию во время компиляции и делает ее доступной для внедрения зависимостей.

В этом руководстве ключом является идентификатор пользователя, а кэшированным значением — полный `UserResponse`.

Такой подход полезен сразу по двум причинам:

- аннотации могут ссылаться на контракт кэша по типу
- сервисы и тесты могут внедрять тот же кэш напрямую и управлять им вручную, когда это нужно

Поскольку контракт расширяет `CaffeineCache<String, UserResponse>`, сгенерированный компонент уже предоставляет операции, которые обычно нужны для управления локальным кэшем.

===! ":fontawesome-brands-java: `Java`"

    Создайте `guides/guide-cache-app/src/main/java/ru/tinkoff/kora/guide/cache/service/UserCaffeineCache.java`:

    ```java
    package ru.tinkoff.kora.guide.cache.service;

    import ru.tinkoff.kora.cache.annotation.Cache;
    import ru.tinkoff.kora.cache.caffeine.CaffeineCache;
    import ru.tinkoff.kora.guide.cache.dto.UserResponse;

    @Cache("cache.caffeine.users")
    public interface UserCaffeineCache extends CaffeineCache<String, UserResponse> {}
    ```

=== ":simple-kotlin: `Kotlin`"

    Создайте `src/main/kotlin/ru/tinkoff/kora/guide/cache/service/UserCaffeineCache.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.cache.service

    import ru.tinkoff.kora.cache.annotation.Cache
    import ru.tinkoff.kora.cache.caffeine.CaffeineCache
    import ru.tinkoff.kora.guide.cache.dto.UserResponse

    @Cache("cache.caffeine.users")
    interface UserCaffeineCache : CaffeineCache<String, UserResponse>
    ```

## `@Cacheable` { #cacheable }

Полные правила `@Cacheable`, `@CachePut`, `@CacheInvalidate` и вычисления ключей описаны в разделах [декларативного кеширования](../documentation/cache.md#declarative) и [ключей кеша](../documentation/cache.md#key).

С этого момента считайте, что приложение запущено **ровно в одном экземпляре**. Это предположение позволяет сосредоточиться на поведении локального Caffeine, пока не решая согласованность кэша между
экземплярами.

Мы все еще сохраняем контракт сервиса из руководства по HTTP-серверу:

- `getUsers()` по-прежнему применяет сортировку и постраничную выдачу
- вспомогательный метод сравнения остается без изменений
- обновление и удаление по-прежнему переводят `boolean`-результаты репозитория в HTTP-ошибки `404`

Kora применяет аннотации кэша через AOP времени компиляции. Для Java это означает, что класс сервиса не должен быть `final`; для Kotlin он должен быть `open`.

`@Cacheable` — самая естественная отправная точка, потому что она моделирует классический путь чтения через кэш:

1. сначала попробовать кэш
2. если значения нет, вызвать исходный метод
3. сохранить результат для следующего вызова

Именно это нам нужно для `getUser()`.

===! ":fontawesome-brands-java: `Java`"

    Обновите только путь чтения в `guides/guide-cache-app/src/main/java/ru/tinkoff/kora/guide/cache/service/UserService.java`:

    ```java
    @Cacheable(UserCaffeineCache.class)
    public Optional<UserResponse> getUser(String id) {
        return userRepository.findById(id);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Обновите только путь чтения в `src/main/kotlin/ru/tinkoff/kora/guide/cache/service/UserService.kt`:

    ```kotlin
    @Cacheable(UserCaffeineCache::class)
    open fun getUser(id: String): UserResponse? {
        return userRepository.findById(id).orElse(null)
    }
    ```

В приложении с **одним экземпляром** это просто и безопасно, когда пользовательские данные читаются гораздо чаще, чем изменяются.

В среде с **N экземплярами** `@Cacheable` по-прежнему работает, но каждый экземпляр приложения заполняет собственный локальный кэш независимо. Это может приводить к:

- неравномерному прогреву между экземплярами
- тому, что разные экземпляры отдают разные кэшированные поколения одной и той же сущности
- большему числу промахов сразу после выката или перезапуска

После компиляции сгенерированный AOP-заместитель показывает путь чтения через кэш:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/guide-cache-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/cache/service/$UserService__AopProxy.java
    ```

    ```java
    private Optional<UserResponse> _getUser_AopProxy_CacheableAopKoraAspect(String id) {
        var _key = id;
        return Optional.ofNullable(userCaffeineCache1.computeIfAbsent(_key, _k -> super.getUser(id).orElse(null)));
    }

    @Override
    public Optional<UserResponse> getUser(String id) {
        return this._getUser_AopProxy_CacheableAopKoraAspect(id);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    guides/kotlin/guide-kotlin-cache-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/cache/service/$UserService__AopProxy.kt
    ```

    ```kotlin
    private fun _getUser_AopProxy_CacheableAopKoraAspect(id: String): UserResponse? {
      val _key = id
      return userCaffeineCache1.computeIfAbsent(_key) { super.getUser(id) }
    }

    override fun getUser(id: String): UserResponse? = _getUser_AopProxy_CacheableAopKoraAspect(id)
    ```

Ключевой момент — `computeIfAbsent(...)`: Kora сначала обращается к кэшу и вызывает `super.getUser(id)` только тогда, когда ключ отсутствует.

## `@CachePut` { #cacheput }

Когда чтения кэшируются, следующая проблема — устаревшие данные после обновлений. `@CachePut` решает ее так: сначала выполняет метод, а затем записывает возвращенное значение в кэш под выбранным
ключом.

Это хорошо подходит для `updateUser()`, потому что после успешного обновления в репозитории мы уже точно знаем, какое значение должно заменить старую запись кэша.

===! ":fontawesome-brands-java: `Java`"

    Обновите только путь обновления в `guides/guide-cache-app/src/main/java/ru/tinkoff/kora/guide/cache/service/UserService.java`:

    ```java
    @CachePut(value = UserCaffeineCache.class, parameters = { "id" })
    public UserResponse updateUser(String id, UserRequest request) {
        boolean updated = userRepository.update(id, request.name(), request.email());
        if (!updated) {
            throw HttpServerResponseException.of(404, "User not found");
        }
        return new UserResponse(id, request.name(), request.email(), LocalDateTime.now());
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Обновите только путь обновления в `src/main/kotlin/ru/tinkoff/kora/guide/cache/service/UserService.kt`:

    ```kotlin
    @CachePut(value = UserCaffeineCache::class, parameters = ["id"])
    open fun updateUser(id: String, request: UserRequest): UserResponse {
        val updated = userRepository.update(id, request.name, request.email)
        if (!updated) {
            throw HttpServerResponseException.of(404, "User not found")
        }
        return UserResponse(id, request.name, request.email, LocalDateTime.now())
    }
    ```

В среде с **N экземплярами** `@CachePut` обновляет только кэш локального экземпляра приложения. Другие экземпляры сохраняют свои прежние значения, пока у них не произойдет промах, истечение срока жизни или инвалидация каким-то другим
механизмом.

Поэтому `@CachePut` отлично подходит для приложений с одним экземпляром и все еще полезен в настройках с несколькими экземплярами, но сам по себе он **не** создает согласованность в масштабе кластера.

После компиляции сгенерированный заместитель показывает, что исходное обновление выполняется до записи в кэш:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/guide-cache-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/cache/service/$UserService__AopProxy.java
    ```

    ```java
    private UserResponse _updateUser_AopProxy_CachePutAopKoraAspect(String id, UserRequest request) {
        var _value = super.updateUser(id, request);
        var _key1 = id;
        userCaffeineCache1.put(_key1, _value);
        return _value;
    }

    @Override
    public UserResponse updateUser(String id, UserRequest request) {
        return this._updateUser_AopProxy_CachePutAopKoraAspect(id, request);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    guides/kotlin/guide-kotlin-cache-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/cache/service/$UserService__AopProxy.kt
    ```

    ```kotlin
    private fun _updateUser_AopProxy_CachePutAopKoraAspect(id: String, request: UserRequest):
        UserResponse {
      val _value = super.updateUser(id, request)
      val _key1 = id
      userCaffeineCache1.put(_key1, _value)
      return _value
    }

    override fun updateUser(id: String, request: UserRequest): UserResponse =
        _updateUser_AopProxy_CachePutAopKoraAspect(id, request)
    ```

Этот порядок важен: если `super.updateUser(...)` завершится ошибкой, кэш не будет обновлен значением, которое на самом деле никогда не было сохранено.

## `@CacheInvalidate` { #cacheinvalidate }

Если запись удалена, самое безопасное действие — полностью удалить кэшированную запись. Именно это делает `@CacheInvalidate`.

Это важно, потому что устаревшая запись кэша после удаления обычно хуже, чем промах кэша: приложение может вернуть сущность, которой уже нет в источнике истины.

===! ":fontawesome-brands-java: `Java`"

    Обновите только путь удаления из кэша в `guides/guide-cache-app/src/main/java/ru/tinkoff/kora/guide/cache/service/UserService.java`:

    ```java
    @CacheInvalidate(UserCaffeineCache.class)
    public void deleteUser(String id) {
        boolean deleted = userRepository.deleteById(id);
        if (!deleted) {
            throw HttpServerResponseException.of(404, "User not found");
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Обновите только путь удаления из кэша в `src/main/kotlin/ru/tinkoff/kora/guide/cache/service/UserService.kt`:

    ```kotlin
    @CacheInvalidate(UserCaffeineCache::class)
    open fun deleteUser(id: String) {
        val deleted = userRepository.deleteById(id)
        if (!deleted) {
            throw HttpServerResponseException.of(404, "User not found")
        }
    }
    ```

В среде с **N экземплярами** действует та же оговорка: инвалидация влияет только на локальный экземпляр кэша. Другие экземпляры могут продолжать отдавать старое значение, пока оно не будет обновлено, не истечет по
сроку жизни или не будет явно инвалидировано более широким механизмом.

После компиляции сгенерированный заместитель показывает, что инвалидация происходит после успешного завершения метода удаления:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/guide-cache-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/cache/service/$UserService__AopProxy.java
    ```

    ```java
    private void _deleteUser_AopProxy_CacheInvalidateAopKoraAspect(String id) {
        super.deleteUser(id);
        var _key1 = id;
        userCaffeineCache1.invalidate(_key1);
    }

    @Override
    public void deleteUser(String id) {
        this._deleteUser_AopProxy_CacheInvalidateAopKoraAspect(id);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    guides/kotlin/guide-kotlin-cache-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/cache/service/$UserService__AopProxy.kt
    ```

    ```kotlin
    private fun _deleteUser_AopProxy_CacheInvalidateAopKoraAspect(id: String) {
      super.deleteUser(id)
      val _key1 = id
      userCaffeineCache1.invalidate(_key1)
      return
    }

    override fun deleteUser(id: String) {
      _deleteUser_AopProxy_CacheInvalidateAopKoraAspect(id)
    }
    ```

Такой сгенерированный порядок предотвращает случайное удаление из кэша до того, как операция удаления действительно завершилась.

## Прогрев кэша { #cache-warmup }

`createUser()` — место, где декларативные аннотации менее удобны. Репозиторий сначала генерирует идентификатор, и только после этого мы узнаем итоговый ключ кэша.

Поэтому в этом руководстве для создания кэш используется императивно:

- сохранить пользователя
- построить итоговый `UserResponse`
- вручную записать это значение в кэш
- вернуть ответ

Это одно из главных преимуществ типизированного контракта кэша: один и тот же кэш можно использовать декларативно в одних методах и напрямую как обычный внедренный компонент в других.

===! ":fontawesome-brands-java: `Java`"

    Обновите только путь создания в `guides/guide-cache-app/src/main/java/ru/tinkoff/kora/guide/cache/service/UserService.java`:

    ```java
    public UserResponse createUser(UserRequest request) {
        var generatedId = userRepository.save(request.name(), request.email());
        var createdUser = new UserResponse(generatedId, request.name(), request.email(), LocalDateTime.now());
        this.userCache.put(createdUser.id(), createdUser);
        return createdUser;
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Обновите только путь создания в `src/main/kotlin/ru/tinkoff/kora/guide/cache/service/UserService.kt`:

    ```kotlin
    fun createUser(request: UserRequest): UserResponse {
        val generatedId = userRepository.save(request.name, request.email)
        val createdUser = UserResponse(generatedId, request.name, request.email, LocalDateTime.now())
        userCache.put(createdUser.id, createdUser)
        return createdUser
    }
    ```

В приложении с **одним экземпляром** это дает немедленный прогрев, поэтому следующее чтение сразу может стать попаданием в кэш.

В среде с **N экземплярами** это по-прежнему прогревает только локальный экземпляр приложения. Другие экземпляры не увидят эту запись, пока сами ее не загрузят.

## Сгенерированный AOP-код { #aop-code }

Сгенерированный AOP-код является реализацией декларативной модели кеширования; подробности см. в разделе [декларативного подхода](../documentation/cache.md#declarative).

Аннотации кэша в этом руководстве также реализованы через AOP времени компиляции.

Это значит, что Kora не переписывает исходный код вашего `UserService` напрямую. Вместо этого она генерирует заместитель на основе подкласса вокруг сервиса и помещает логику кэширования в этот
сгенерированный класс. Метод вашего сервиса по-прежнему выглядит как обычный бизнес-код, но сгенерированный заместитель решает, когда:

- проверить кэш перед вызовом исходного метода
- сохранить возвращенное значение в кэш
- инвалидировать запись кэша после успешного вызова метода

Именно поэтому здесь действует то же правило AOP:

- в Java аннотированный класс сервиса не должен быть `final`
- в Kotlin аннотированный класс сервиса и аннотированные методы должны быть `open`

После запуска:

```bash
./gradlew clean classes
```

вы можете посмотреть сгенерированный заместитель здесь:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/guide-cache-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/cache/service/$UserService__AopProxy.java
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    guides/kotlin/guide-kotlin-cache-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/cache/service/$UserService__AopProxy.kt
    ```

Этот файл — лучшее место, чтобы увидеть, что Kora на самом деле сгенерировала для:

- `@Cacheable`
- `@CachePut`
- `@CacheInvalidate`

В предыдущих главах о кэше сгенерированные фрагменты были показаны рядом с аннотацией, которая их породила. Этот финальный раздел о сгенерированном коде — карта для отладки: откройте заместитель и
найдите метод сервиса, поведение кэша которого хотите проверить.

Если вам интересно посмотреть на саму сгенерированную реализацию кэша, также можно открыть:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/guide-cache-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/cache/service/$UserCaffeineCacheImpl.java
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    guides/kotlin/guide-kotlin-cache-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/cache/service/$UserCaffeineCacheModule.kt
    ```

Вместе эти сгенерированные исходники упрощают понимание руководства:

- заместитель показывает, как оборачиваются аннотированные методы сервиса
- реализация кэша показывает, как типизированный контракт кэша материализуется для внедрения зависимостей

## Конфигурация { #config }

Сохраните конфигурацию HTTP-сервера из предыдущего руководства и добавьте раздел Caffeine, который соответствует контракту `@Cache("cache.caffeine.users")`.

Обновите `guides/guide-cache-app/src/main/resources/application.conf`:

Полное описание настроек смотрите в разделе [Кэш](../documentation/cache.md).

===! ":material-code-json: `Hocon`"

    ```javascript
    cache.caffeine.users {
      maximumSize = 1000 //(1)!
      expireAfterWrite = "10m" //(2)!
    }
    ```

    1. Максимальное число записей кэша, после которого начинается вытеснение.
    2. Время, через которое запись истекает после записи.

=== ":simple-yaml: `YAML`"

    ```yaml
    cache:
      caffeine:
        users:
          maximumSize: 1000 #(1)!
          expireAfterWrite: "10m" #(2)!
    ```

    1. Максимальное число записей кэша, после которого начинается вытеснение.
    2. Время, через которое запись истекает после записи.

## Запуск приложения { #run-app }

Используйте стандартный процесс запуска:

```bash
./gradlew clean classes
./gradlew test
./gradlew run
```

## Проверка приложения { #check-app }

Начните с создания пользователя:

```bash
curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -H "X-Request-ID: req-1" \
  -H "User-Agent: curl" \
  -b "sessionId=test-session" \
  -d '{"name":"John Doe","email":"john@example.com"}'
```

Затем прочитайте того же пользователя дважды. Первый запрос загрузит его из репозитория, а второй повторно использует запись кэша.

```bash
curl http://localhost:8080/users/1
curl http://localhost:8080/users/1
```

Обновите пользователя. Это обновит кэшированное значение через `@CachePut`.

```bash
curl -X PUT http://localhost:8080/users/1 \
  -H "Content-Type: application/json" \
  -d '{"name":"John Updated","email":"john.updated@example.com"}'
```

Удалите пользователя. Это удалит устаревшую запись кэша через `@CacheInvalidate`.

```bash
curl -X DELETE http://localhost:8080/users/1
```

Также можно проверить, что конечная точка списка из базового HTTP-руководства по-прежнему работает без изменений:

```bash
curl "http://localhost:8080/users?page=0&size=10&sort=name"
```

## Лучшие практики { #best-practices }

- Сначала кэшируйте стабильные пути чтения, затем явно добавляйте обновление или инвалидацию на стороне записи.
- Держите ключи кэша простыми и предсказуемыми. Здесь ключ — это только идентификатор пользователя.
- Прогревайте кэш вручную только тогда, когда аннотации не могут естественно вывести ключ, например после генерации идентификатор в `createUser()`.
- Предпочитайте локальные кэши Caffeine для ускорения каждого экземпляра, а не для глобально общего состояния.
- Относитесь к типизированному контракту кэша как к части проектирования, а не просто как к украшению фреймворка.

## Итоги { #summary }

Вы расширили руководство по HTTP-серверу локальным типизированным кэшем Caffeine и сохранили существующий контракт API `/users` без изменений.

Итоговое приложение теперь использует:

- императивный прогрев кэша в `createUser()`
- декларативное кэширование чтения в `getUser()`
- декларативное обновление кэша в `updateUser()`
- декларативную инвалидацию в `deleteUser()`
- типизированный контракт кэша, который можно и аннотировать, и внедрять напрямую
- сгенерированный AOP-заместитель, который применяет аннотации кэша вокруг методов сервиса

## Ключевые понятия { #key-concepts }

- кэш — это быстрый вторичный слой хранения для повторных чтений
- локальные кэши в памяти улучшают один экземпляр приложения или один процесс за раз
- `CaffeineCache<K, V>` дает типизированный контракт кэша, который Kora реализует во время компиляции
- `@Cacheable`, `@CachePut` и `@CacheInvalidate` покрывают самые частые потоки чтения, обновления и удаления из кэша
- императивное и декларативное кэширование можно сочетать в одном сервисе, когда разным методам нужен разный контроль над моментом работы с кэшем
- исходник сгенерированного `$UserService__AopProxy` точно показывает, как Kora оборачивает аннотированные методы

## Устранение неполадок { #troubleshooting }

**Аннотации кэша не работают:**

Убедитесь, что класс сервиса не `final` в Java и `open` в Kotlin. Аспекты кэша Kora применяются через AOP времени компиляции и требуют цель, от которой можно наследоваться.

**Я хочу увидеть, где на самом деле выполняются аннотации кэша:**

Запустите:

```bash
./gradlew clean classes
```

Затем откройте:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/guide-cache-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/cache/service/$UserService__AopProxy.java
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    guides/kotlin/guide-kotlin-cache-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/cache/service/$UserService__AopProxy.kt
    ```

Этот сгенерированный файл показывает, где Kora вставляет проверки кэша, записи в кэш и логику инвалидации вокруг исходных методов `UserService`.

**Кэш никогда не обновляется после создания:**

`createUser()` генерирует идентификатор после вызова репозитория, поэтому нужен ручной `userCache.put(createdUser.id(), createdUser)`, если вы хотите закэшировать новую сущность до первого чтения.

**Gradle зависает или неожиданно завершается ошибкой:**

Остановите запущенные демоны Gradle и повторите:

```bash
./gradlew --stop
./gradlew clean classes
```

**Windows `AccessDeniedException` в кэше Gradle:**

Если Windows удерживает открытые файловые дескрипторы в `.gradle` или `build/`, остановите демоны Gradle, закройте процессы среда разработки, которые все еще следят за каталогом, и повторно выполните команду.

**Ошибки контекста сборки Docker в последующих тестах по принципу черного ящика:**

Если позже вы упакуете это приложение для тестирования как черный ящик, убедитесь, что `Dockerfile` использует каталог модуля как свой контекст сборки. Ошибки вроде `COPY failed` обычно означают, что
сборка была запущена из неправильной папки.

**Проверки готовности падают на последующих шагах наблюдаемости:**

Если вы продолжите это приложение наблюдаемостью, помните, что готовность проверяется на `http://localhost:8085/system/readiness`, а не на общедоступном порту `8080`.

## Что дальше? { #whats-next }

- [Многоуровневый кэш](cache-multi-level.md), чтобы объединить локальный кэш Caffeine с распределенным кэшем Redis.
- [Шаблоны отказоустойчивости](resilient.md), чтобы защищать дорогие нижележащие вызовы до того, как их результаты будут закэшированы.
- [Наблюдаемость](observability.md), чтобы измерять пути запросов с кэшем с помощью метрик и трассировок.
- [Тестирование с JUnit](testing-junit.md), чтобы добавить точечные компонентные проверки вокруг кэшируемых сервисов.

## Помощь { #help }

Если возникли проблемы:

- сравните с [Kora Java Cache App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-cache-app) и [Kora Kotlin Cache App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-cache-app)
- проверьте [документацию по кэшу](../documentation/cache.md)
- проверьте [пример Caffeine](https://github.com/kora-projects/kora-examples/tree/master/kora-java-cache-caffeine)
- вернитесь к [Базе данных JDBC](database-jdbc.md), если поведение репозитория непонятно
