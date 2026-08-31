---
search:
  exclude: true
title: Многоуровневое кеширование с Redis
summary: Learn how to extend the Caffeine cache guide with Redis as a shared second-level cache for Kora applications
description: "Step-by-step two-level caching for a Kora 2.0 service: keeping the Caffeine L1 cache from the cache guide and adding a shared Redis L2 cache through the io.koraframework:cache-redis-lettuce artifact and LettuceRedisCacheModule, a second @Cache contract extending RedisCache<String, @Json UserResponse>, stacked @Cacheable, @CachePut with the args attribute and @CacheInvalidate annotations applied in declaration order, imperative warm-up of both levels, and the cache.caffeine, cache.redis and lettuce configuration sections."
agent:
  use_when: "Use this file for questions about layering a shared Redis cache under a local Caffeine cache in a Kora 2.0 service: io.koraframework:cache-redis-lettuce, LettuceRedisCacheModule, RedisCache<K, @Json V> and why the @Json goes on the value type parameter, stacking @Cacheable / @CachePut / @CacheInvalidate for L1 then L2, the args attribute that selects key parameters, @CacheInvalidateAll, CacheMode SYNC and ASYNC, CacheKeyMapper with @Mapping, the cache.redis.* keys (keyPrefix, expireAfterWrite, expireAfterAccess) and the lettuce.* client section (uri, user, password, database, protocol, socketTimeout, commandTimeout)."
tags: caching, redis, caffeine, multi-level, distributed, performance
---

# Многоуровневое кеширование с Redis { #multi-level-caching-redis }

Это руководство знакомит с многоуровневым кешированием в Kora, Caffeine и Redis. В нем рассматривается, как быстрый локальный кеш L1 и общий кеш Redis L2 работают вместе, как Kora объединяет
реализации кеша за одним кеш-договором, и как аннотации кеширования на уровне сервиса сохраняют чтения и инвалидацию согласованными. Вы также увидите, почему Redis рассматривается как общая
инфраструктура кеширования, а не как источник истины.

===! ":fontawesome-brands-java: `Java`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Java Cache Multi Level App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-cache-multi-level-app).

=== ":simple-kotlin: `Kotlin`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Kotlin Cache Multi Level App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-cache-multi-level-app).

## Что вы создадите { #youll-build }

В этом руководстве вы превратите одноуровневый кеш из предыдущего руководства в двухуровневый, где:

- `UserCaffeineCache` остается быстрым локальным кешем L1
- `UserRedisCache` становится общим кешем L2
- `getUser()` сначала проверяет Caffeine, затем Redis, затем репозиторий
- `createUser()` сразу прогревает оба уровня кеша
- `updateUser()` обновляет оба уровня кеша
- `deleteUser()` вытесняет устаревшие данные с обоих уровней
- HTTP API `/users` остается прежним, а поведение кеша становится дружелюбным к нескольким экземплярам

## Что понадобится { #youll-need }

- JDK 25 или новее
- Gradle 9+
- текстовый редактор или среда разработки
- Docker или другая локальная среда исполнения Redis
- пройденное руководство [Стратегии кеширования с Kora](cache.md)

## Требования { #prerequisites }

!!! note "Обязательно: пройдите руководство по кешированию"

    Это руководство предполагает, что вы прошли **[Стратегии кеширования с Kora](cache.md)** и у вас уже есть те же `Application`, `UserController`, `UserService`, DTO и контракт `UserCaffeineCache` из того руководства.

    Если вы еще не прошли руководство по кешированию, сначала сделайте это, потому что здесь сохраняется тот же API `/users` и добавляется Redis как второй уровень кеша.

## Обзор { #overview }

В предыдущем руководстве использовался только **локальный кеш в памяти**. Это хорошо работает, когда приложение выполняется в одной JVM, потому что каждое повторное чтение обслуживается из локальной
памяти.

Но как только приложение работает в нескольких подах или экземплярах, одного локального кеша для части нагрузок становится недостаточно:

- у каждого пода собственное содержимое кеша
- значение, прогретое в поде A, не становится автоматически видимым в поде B
- обновление, обработанное подом A, не обновляет локальную память пода B
- после перезапуска под снова стартует с пустым локальным кешем

Поэтому распространенный следующий шаг — **многоуровневое кеширование**.

В этом руководстве мы используем два уровня:

1. **L1: Caffeine**
   Это тот же локальный кеш в памяти из предыдущего руководства. Он самый быстрый и идеален для горячих повторных чтений внутри одного процесса.
2. **L2: Redis**
   Это общий распределенный кеш. Он медленнее локальной памяти, но все равно намного быстрее, чем каждый раз ходить к первоисточнику.

Типичный поток чтения теперь такой:

1. Сначала пробуем Caffeine.
2. Если Caffeine промахнулся, пробуем Redis.
3. Если Redis тоже промахнулся, загружаем из репозитория.
4. Кладем значение обратно в кеш, чтобы последующие чтения были дешевле.

Такая слоеная модель полезна тем, что балансирует скорость и совместное использование:

- Caffeine дает минимальную задержку для горячих значений внутри одного пода.
- Redis позволяет разным подам переиспользовать одно и то же закешированное значение.
- Репозиторий остается источником истины, когда оба кеша промахнулись.

### Redis как L2-кеш { #redis-l2 }

Redis — популярный кеш второго уровня, потому что он дает:

- доступ в памяти с низкой задержкой
- общее состояние между экземплярами
- истечение срока ключей и префиксы ключей
- зрелый эксплуатационный инструментарий
- простое развертывание для локальной разработки и промышленной среды

В этом руководстве Redis не считается источником истины. Он остается кешем. Репозиторий по-прежнему авторитетен, а Redis лишь помогает разным экземплярам приложения не повторять одни и те же
обращения.

### Модель кеша Kora { #cache-model }

Полная модель составного кеша описана в [Составном кеше](../documentation/cache.md#composite-cache), а слой Redis — в разделе [Redis](../documentation/cache.md#redis).

Поддержка кеша в Kora хорошо подходит для слоеных кешей, потому что кеш-договоры типизированы, а аннотации кеширования компонуемы.

Это значит, что можно определить два отдельных кеш-интерфейса:

- `UserCaffeineCache extends CaffeineCache<String, UserResponse>`
- `UserRedisCache extends RedisCache<String, @Json UserResponse>`

А затем разместить несколько аннотаций на одном методе сервиса:

- `@Cacheable(UserCaffeineCache.class)`
- `@Cacheable(UserRedisCache.class)`

`@Cacheable`, `@CachePut`, `@CacheInvalidate` и `@CacheInvalidateAll` — все `@Repeatable`, что и делает такое наслоение допустимым. Kora применяет их в порядке объявления, сверху вниз. То есть на
практике:

- сначала проверяется L1 Caffeine
- затем L2 Redis
- затем выполняется исходный метод, если оба промахнулись

Та же идея работает для `@CachePut` и `@CacheInvalidate`, а поскольку порядок — это порядок объявления, перестановка двух строк меняет местами уровни.

## Зависимости { #dependencies }

Добавьте кеширование Redis в приложение из руководства по кешированию.

===! ":fontawesome-brands-java: `Java`"

    Добавьте в блок `dependencies` в `build.gradle`:

    ```groovy
    dependencies {
        // ... existing dependencies ...

        implementation("io.koraframework:cache-redis-lettuce")
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Добавьте в блок `dependencies` в `build.gradle.kts`:

    ```kotlin
    dependencies {
        // ... existing dependencies ...

        implementation("io.koraframework:cache-redis-lettuce")
    }
    ```

Имя артефакта стоит прочитать внимательно. `cache-redis-lettuce` — это **реализация** поверх Lettuce; она приносит с собой общие контракты `cache-redis-common` (`RedisCache`, `RedisCacheConfig`) и сам
клиент Lettuce, поэтому строка добавляется только одна. `cache-caffeine` из предыдущего руководства остается ровно таким же: два бэкенда кеша — независимые артефакты, и ни один не заменяет другой.

## Модули { #modules }

Базовое руководство по кешированию уже включает `CaffeineCacheModule`. Для многоуровневого кеша графу приложения нужен еще и `LettuceRedisCacheModule`.

===! ":fontawesome-brands-java: `Java`"

    Обновите `src/main/java/io/koraframework/guide/cache/Application.java`:

    ```java
    package io.koraframework.guide.cache;

    import io.koraframework.application.graph.KoraApplication;
    import io.koraframework.cache.caffeine.CaffeineCacheModule;
    import io.koraframework.cache.redis.lettuce.LettuceRedisCacheModule;
    import io.koraframework.common.annotation.KoraApp;
    import io.koraframework.config.hocon.HoconConfigModule;
    import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule;
    import io.koraframework.json.common.JsonModule;
    import io.koraframework.logging.logback.LogbackModule;

    @KoraApp
    public interface Application extends
            HoconConfigModule,
            JsonModule,
            LogbackModule,
            UndertowPublicHttpServerModule,
            CaffeineCacheModule,        // <----- Connected module
            LettuceRedisCacheModule {   // <----- Connected module

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Обновите `src/main/kotlin/io/koraframework/guide/cache/Application.kt`:

    ```kotlin
    package io.koraframework.guide.cache

    import io.koraframework.application.graph.KoraApplication
    import io.koraframework.cache.caffeine.CaffeineCacheModule
    import io.koraframework.cache.redis.lettuce.LettuceRedisCacheModule
    import io.koraframework.common.annotation.KoraApp
    import io.koraframework.config.hocon.HoconConfigModule
    import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule
    import io.koraframework.json.common.JsonModule
    import io.koraframework.logging.logback.LogbackModule

    @KoraApp
    interface Application :
        HoconConfigModule,
        JsonModule,
        LogbackModule,
        UndertowPublicHttpServerModule,
        CaffeineCacheModule,       // <----- Connected module
        LettuceRedisCacheModule    // <----- Connected module

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

`LettuceRedisCacheModule` строит клиент Redis из верхнеуровневой секции конфигурации `lettuce`, публикует `RedisCacheClient`, которым пользуются сгенерированные кеши, и добавляет помеченные мапперы
ключей и значений, благодаря которым типы значений с `@Json` работают без дополнительной обвязки. `JsonModule` по-прежнему должен быть в графе, потому что эти мапперы значений делегируют
сгенерированным JSON-писателю и читателю вашего DTO.

## Контракт многоуровневого кеша { #cache-contract }

Подробнее о кешах Redis, сериализации значений и типизированных кеш-договорах — в [документации по кешу Redis](../documentation/cache.md#redis).

В предыдущем руководстве уже определен `UserCaffeineCache`. Теперь добавим второй контракт — для Redis.

Этот контракт важен по двум причинам:

- аннотации могут ссылаться на него декларативно
- тот же кеш можно внедрить напрямую, когда нужно ручное управление

Кеш Caffeine хранит Java-объекты прямо в локальной памяти, поэтому может держать `UserResponse` как есть. С Redis иначе: значения нужно сериализовать перед записью в Redis и десериализовать при
чтении.

Чтобы этот шаблон чисто работал в Kora:

- сохраните `@Json` на DTO, чтобы Kora сгенерировала для полезной нагрузки читатель и писатель
- пометьте **параметр типа значения** кеша Redis как `@Json UserResponse`, чтобы кеш-договор явно говорил, в каком сериализованном виде Redis хранит данные

Эта вторая `@Json` — аннотация на использовании типа, записанная внутри списка обобщенных аргументов, а не на интерфейсе. Именно она выбирает помеченный `@Json` `RedisCacheValueMapper`, который дает
`LettuceRedisCacheModule`, и без нее у графа нет способа превратить `UserResponse` в байты.

Тот же механизм гибок: подойдет любая метка и для типа ключа, и для типа значения, лишь бы в графе существовал маппер с этой меткой. `@Json` — просто та метка, которую Kora поставляет из коробки.

В рабочем приложении Redis хранит `UserResponse`, поэтому контракт использует `String` как ключ и `@Json UserResponse` как тип значения.

===! ":fontawesome-brands-java: `Java`"

    Создайте `src/main/java/io/koraframework/guide/cache/service/UserRedisCache.java`:

    ```java
    package io.koraframework.guide.cache.service;

    import io.koraframework.cache.annotation.Cache;
    import io.koraframework.cache.redis.RedisCache;
    import io.koraframework.guide.cache.dto.UserResponse;
    import io.koraframework.json.common.annotation.Json;

    @Cache("cache.redis.users")
    public interface UserRedisCache extends RedisCache<String, @Json UserResponse> {
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Создайте `src/main/kotlin/io/koraframework/guide/cache/service/UserRedisCache.kt`:

    ```kotlin
    package io.koraframework.guide.cache.service

    import io.koraframework.cache.annotation.Cache
    import io.koraframework.cache.redis.RedisCache
    import io.koraframework.guide.cache.dto.UserResponse
    import io.koraframework.json.common.annotation.Json

    @Cache("cache.redis.users")
    interface UserRedisCache : RedisCache<String, @Json UserResponse>
    ```

Обратите внимание, что `RedisCache` приходит из `io.koraframework.cache.redis` — общего пакета контрактов, а не из пакета `lettuce`. Контракт остается тем же, какую бы реализацию клиента Redis вы ни
подключили, так что Lettuce называет только модуль в `Application`.

Как и в контракте Caffeine, значение `@Cache` — это путь конфигурации, поэтому `cache.redis.users` должен существовать в `application.conf` до того, как граф сможет собраться.

## Реализация многоуровневого кеша { #cache-impl }

Сервис продолжает тот, что был в руководстве по кешированию. Неизмененные части ведут себя так же:

- `getUsers()` по-прежнему применяет сортировку и постраничную выдачу
- вспомогательный компаратор остается тем же
- поведение `404` на стороне HTTP по-прежнему живет в сервисе

Здесь мы показываем только методы, которые меняются ради многоуровневого кеширования:

- `getUser()` — `@Cacheable` объявлена дважды, чтобы Kora проверяла сначала Caffeine, потом Redis.
- `updateUser()` — `@CachePut` объявлена дважды, чтобы оба уровня обновились после успешного обновления.
- `deleteUser()` — `@CacheInvalidate` объявлена дважды, чтобы оба уровня вытеснили устаревшее значение.

===! ":fontawesome-brands-java: `Java`"

    Обновите изменившиеся методы в `src/main/java/io/koraframework/guide/cache/service/UserService.java`:

    ```java
    @Cacheable(UserCaffeineCache.class)
    @Cacheable(UserRedisCache.class)
    public Optional<UserResponse> getUser(String id) {
        return userRepository.findById(id);
    }

    @CachePut(value = UserCaffeineCache.class, args = { "id" })
    @CachePut(value = UserRedisCache.class, args = { "id" })
    public UserResponse updateUser(String id, UserRequest request) {
        boolean updated = userRepository.update(id, request.name(), request.email());
        if (!updated) {
            throw HttpServerResponseException.of(404, "User not found");
        }
        return new UserResponse(id, request.name(), request.email(), LocalDateTime.now());
    }

    @CacheInvalidate(UserCaffeineCache.class)
    @CacheInvalidate(UserRedisCache.class)
    public void deleteUser(String id) {
        boolean deleted = userRepository.deleteById(id);
        if (!deleted) {
            throw HttpServerResponseException.of(404, "User not found");
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Обновите изменившиеся методы в `src/main/kotlin/io/koraframework/guide/cache/service/UserService.kt`:

    ```kotlin
    @Cacheable(UserCaffeineCache::class)
    @Cacheable(UserRedisCache::class)
    open fun getUser(id: String): UserResponse? = userRepository.findById(id)

    @CachePut(value = UserCaffeineCache::class, args = ["id"])
    @CachePut(value = UserRedisCache::class, args = ["id"])
    open fun updateUser(id: String, request: UserRequest): UserResponse {
        if (!userRepository.update(id, request.name, request.email)) {
            throw HttpServerResponseException.of(404, "User not found")
        }
        return UserResponse(id, request.name, request.email, LocalDateTime.now())
    }

    @CacheInvalidate(UserCaffeineCache::class)
    @CacheInvalidate(UserRedisCache::class)
    open fun deleteUser(id: String) {
        if (!userRepository.deleteById(id)) {
            throw HttpServerResponseException.of(404, "User not found")
        }
    }
    ```

Атрибут, выбирающий параметры ключа, — это `args`. `updateUser(String id, UserRequest request)` принимает два аргумента, но частью ключа кеша является только `id`, поэтому `args = { "id" }` сужает
выбор. Без `args` частью ключа стал бы каждый параметр, а для `updateUser` это дало бы ключ, который не совпал бы ни с одним чтением. `getUser` и `deleteUser` в `args` не нуждаются, потому что их
единственный параметр и есть ключ.

Набор дополняют две родственные аннотации. `@CacheInvalidateAll(UserRedisCache.class)` очищает весь кеш, а не один ключ, — правильный инструмент после массового импорта. А каждая аннотация кеширования
принимает `mode = CacheMode.ASYNC`, что позволяет выполнить запись в кеш вне вызывающего потока, когда задержка самого метода важнее, чем то, чтобы запись успела до его возврата.

В среде из N подов это заметно меняет поведение по сравнению с только локальным кешем:

- промах в одном поде все еще может стать попаданием в Redis
- повторные чтения в том же поде по-прежнему выигрывают от скорости локального Caffeine
- обновления и удаления теперь обновляют или вытесняют общий уровень кеша, а не только память одного пода

Обратите внимание, чего наслоение **не** дает: попадание в Caffeine не обновляет Redis, а попадание в Redis не наполняет Caffeine. Каждый уровень опрашивается и пишется независимо, так что запись,
вытесненная из L1 по `maximumSize`, при следующем чтении отдается из L2, но остается отсутствующей в L1, пока туда что-нибудь ее не запишет.

## Прогрев кеша { #cache-warmup }

`createUser()` по-прежнему требует ручного управления кешем, потому что идентификатор пользователя сначала генерирует репозиторий.

Это один из самых наглядных примеров того, зачем нужны типизированные кеш-договоры: те же кеши, что используют аннотации, можно внедрить и управлять ими напрямую.

===! ":fontawesome-brands-java: `Java`"

    Обновите путь создания в `src/main/java/io/koraframework/guide/cache/service/UserService.java`:

    ```java
    public UserResponse createUser(UserRequest request) {
        var generatedId = userRepository.save(request.name(), request.email());
        var createdUser = new UserResponse(generatedId, request.name(), request.email(), LocalDateTime.now());
        this.userCaffeineCache.put(createdUser.id(), createdUser);
        this.userRedisCache.put(createdUser.id(), createdUser);
        return createdUser;
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Обновите путь создания в `src/main/kotlin/io/koraframework/guide/cache/service/UserService.kt`:

    ```kotlin
    fun createUser(request: UserRequest): UserResponse {
        val generatedId = userRepository.save(request.name, request.email)
        val createdUser = UserResponse(generatedId, request.name, request.email, LocalDateTime.now())
        userCaffeineCache.put(createdUser.id, createdUser)
        userRedisCache.put(createdUser.id, createdUser)
        return createdUser
    }
    ```

Оба кеша — обычные зависимости конструктора `UserService`, внедряемые рядом с `UserRepository`. Так следующее чтение сразу обслуживается из кеша, а в Redis уже лежит новая сущность и для других
экземпляров.

Если ключ кеша не является одним из параметров метода — составной ключ или значение, выведенное из аргумента, — декларативный путь состоит в `CacheKeyMapper`, привязанном через `@Mapping`, а не в
императивном `put`. Маппер без зависимостей конструктора создается сгенерированным кодом и больше ничего не требует; маппер, который что-то внедряет, обязан быть еще и `@Component`, чтобы граф мог его
предоставить. Смотрите [Составной ключ](../documentation/cache.md#composite-key).

## Конфигурация { #config }

Оставьте настройку HTTP-сервера из предыдущего руководства как есть. Здесь мы обновляем только конфигурацию кешей и клиента Redis.

Обновите `src/main/resources/application.conf`:

Полный справочник по конфигурации смотрите в [Кеше](../documentation/cache.md).

===! ":material-code-json: `Hocon`"

    ```javascript
    cache.caffeine.users {
      maximumSize = 1000 //(1)!
      expireAfterWrite = "10m" //(2)!
    }

    cache.redis.users {
      keyPrefix = "users-" //(3)!
      expireAfterWrite = "30m" //(4)!
    }

    lettuce {
      uri = "redis://localhost:6379" //(5)!
      uri = ${?REDIS_URL} //(6)!
      user = ${?REDIS_USER} //(7)!
      password = ${?REDIS_PASS} //(8)!
      socketTimeout = 15s //(9)!
      commandTimeout = 15s //(10)!
    }
    ```

    1. Максимальное число записей в кеше до начала вытеснения.
    2. Время, после которого запись Caffeine истекает, считая от записи.
    3. Префикс, добавляемый к ключам, сохраняемым в Redis. Обязателен.
    4. Время, после которого запись Redis истекает, считая от записи.
    5. URI подключения к локальному Redis по умолчанию.
    6. URI подключения. Необязательное переопределение из `REDIS_URL`.
    7. Имя пользователя для подключения клиента. Необязательное переопределение из `REDIS_USER`.
    8. Пароль пользователя базы. Необязательное переопределение из `REDIS_PASS`.
    9. Таймаут операций сокета *(по умолчанию: `10s`)*.
    10. Таймаут выполнения команды Redis *(по умолчанию: `30s`)*.

=== ":simple-yaml: `YAML`"

    ```yaml
    cache:
      caffeine:
        users:
          maximumSize: 1000 #(1)!
          expireAfterWrite: "10m" #(2)!
      redis:
        users:
          keyPrefix: "users-" #(3)!
          expireAfterWrite: "30m" #(4)!
    lettuce:
      uri: ${?REDIS_URL:"redis://localhost:6379"} #(5)!
      user: ${?REDIS_USER} #(6)!
      password: ${?REDIS_PASS} #(7)!
      socketTimeout: 15s #(8)!
      commandTimeout: 15s #(9)!
    ```

    1. Максимальное число записей в кеше до начала вытеснения.
    2. Время, после которого запись Caffeine истекает, считая от записи.
    3. Префикс, добавляемый к ключам, сохраняемым в Redis. Обязателен.
    4. Время, после которого запись Redis истекает, считая от записи.
    5. URI подключения с локальным значением по умолчанию и необязательным переопределением из `REDIS_URL`.
    6. Имя пользователя для подключения клиента. Необязательное переопределение из `REDIS_USER`.
    7. Пароль пользователя базы. Необязательное переопределение из `REDIS_PASS`.
    8. Таймаут операций сокета *(по умолчанию: `10s`)*.
    9. Таймаут выполнения команды Redis *(по умолчанию: `30s`)*.

Параметры, которые принимает секция кеша Redis:

| Параметр                    | Описание                                                           | По умолчанию   |
|-----------------------------|--------------------------------------------------------------------|----------------|
| `enabled`                   | Выключает кеш, не удаляя его из кода                                | `true`         |
| `keyPrefix`                 | Строка, добавляемая перед каждым ключом, который пишет этот кеш      | *(обязательный, без значения по умолчанию)* |
| `expireAfterWrite`          | Время, после которого запись удаляется, считая от записи             | *(опционально)*|
| `expireAfterAccess`         | Время, после которого запись удаляется, считая от последнего чтения  | *(опционально)*|
| `telemetry.logging.enabled` | Логирует операции кеша                                              | `false`        |
| `telemetry.metrics.enabled` | Регистрирует метрики кеша в реестре метрик                          | `false`        |
| `telemetry.tracing.enabled` | Создает спан на каждую операцию кеша                                | `true`         |

Здесь важны несколько деталей:

- `cache.caffeine.users` соответствует `UserCaffeineCache`, а `cache.redis.users` — `UserRedisCache`. Каждому контракту `@Cache` нужна своя секция.
- `lettuce` — одна верхнеуровневая секция, общая для всех кешей Redis в приложении. Она описывает *подключение*, а не какой-то один кеш, и принимает еще `database`, `protocol` (по умолчанию `RESP3`) и настройки `ssl`.
- `keyPrefix` обязателен и предотвращает конфликты внутри экземпляра Redis, который делят с другими кешами или приложениями.
- `REDIS_URL` позволяет тестам или другим средам переопределить локальный URI по умолчанию.

## Docker Compose { #docker-compose }

Для локальных запусков по руководству проще всего небольшой файл Docker Compose.

Создайте `docker-compose.yml` в каталоге модуля приложения:

```yaml
services:
    redis:
        image: redis:8.2-alpine
        ports:
            - "6379:6379"
        command: redis-server --save 60 1 --appendonly yes
        healthcheck:
            test: [ "CMD", "redis-cli", "ping" ]
            interval: 10s
            timeout: 3s
            retries: 5
```

Запустите Redis:

```bash
docker compose up -d redis
```

Проверьте, что он здоров:

```bash
docker compose ps
```

## Запуск приложения { #run-app }

Используйте стандартный порядок из руководств:

```bash
./gradlew clean classes
./gradlew test
./gradlew run
```

Рабочий модуль-компаньон также проверяет многоуровневое поведение точечными компонентными тестами поверх Redis.

## Проверка приложения { #check-app }

Сначала создайте пользователя:

```bash
curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -d '{"name":"John Doe","email":"john@example.com"}'
```

Прочитайте того же пользователя дважды. Второй запрос должен обслуживаться из кеша, а в реальном развертывании с несколькими экземплярами Redis дает общий запасной вариант, когда другой экземпляр
промахивается мимо своего локального Caffeine.

```bash
curl http://localhost:8080/users/1
curl http://localhost:8080/users/1
```

Обновите пользователя. Оба уровня кеша обновляются:

```bash
curl -X PUT http://localhost:8080/users/1 \
  -H "Content-Type: application/json" \
  -d '{"name":"John Updated","email":"john.updated@example.com"}'
```

Удалите пользователя. Оба уровня кеша инвалидируются:

```bash
curl -X DELETE http://localhost:8080/users/1
```

Чтобы увидеть уровень L2 напрямую, загляните внутрь Redis. Ключ — это `keyPrefix`, за которым идет ключ кеша:

```bash
docker compose exec redis redis-cli KEYS 'users-*'
```

Если после этого хотите остановить локальный Redis:

```bash
docker compose down
```

## Лучшие практики { #best-practices }

- Держите Caffeine первым уровнем кеша для горячих внутрипроцессных чтений.
- Используйте Redis как общий уровень кеша, а не как замену источнику истины.
- Делайте кеш-договоры типизированными и явными, чтобы их можно было использовать и декларативно, и императивно.
- Ставьте `@Json` на **параметр типа значения** Redis, а не только на класс DTO: именно это выбирает помеченный маппер значений.
- Давайте каждому кешу Redis отдельный `keyPrefix`, ведь один экземпляр Redis обычно общий.
- Называйте параметры ключа через `args` всякий раз, когда метод принимает больше аргументов, чем нужно ключу.
- Держите семантику обновления кеша близкой к бизнес-операциям: обновлять при обновлении, вытеснять при удалении, прогревать явно при создании.
- Задавайте `expireAfterWrite` на уровне Redis, даже если уровень Caffeine уже истекает: запись в L2 переживает любой перезапуск пода.

## Итоги { #summary }

Вы развили одноуровневое руководство по кешированию в многоуровневую архитектуру кеша.

Получившееся приложение теперь использует:

- локальный `UserCaffeineCache` для сверхбыстрых повторных чтений внутри одного экземпляра
- общий `UserRedisCache` для переиспользования между экземплярами
- слоеные чтения `@Cacheable`
- слоеные обновления `@CachePut`
- слоеные вытеснения `@CacheInvalidate`
- ручной прогрев обоих кешей в `createUser()`

## Ключевые понятия { #key-concepts }

- многоуровневое кеширование сочетает выигрыш локальной задержки с общим распределенным переиспользованием
- Caffeine и Redis решают разные задачи и хорошо работают вместе, а их артефакты независимы
- `cache-redis-lettuce` дает `LettuceRedisCacheModule`, а контракт `RedisCache` живет в общем пакете `io.koraframework.cache.redis`
- Kora применяет несколько аннотаций кеширования в порядке объявления, и именно это заставляет работать схему «сначала L1, потом L2»
- значениям кеша Redis для собственных DTO нужна `@Json` на параметре типа значения, чтобы разрешился помеченный маппер значений
- `@CachePut` и родственные аннотации выбирают параметры ключа через атрибут `args`
- типизированные кеш-договоры можно внедрять напрямую для ручного управления кешем

## Устранение неполадок { #troubleshooting }

**Сборка графа падает на `RedisCacheValueMapper<...>`:**

Если вы кешируете собственное DTO в Redis, убедитесь, что кеш-договор Redis использует `@Json` на типе значения, например:

```java
public interface UserRedisCache extends RedisCache<String, @Json UserResponse> {
}
```

Без этого у Kora нет помеченного маппера для вашего DTO и она не может сгенерировать кеш Redis. Проверьте также, что `JsonModule` по-прежнему в графе, а сам `UserResponse` помечен `@Json`.

**Зависимость на простой артефакт `cache-redis` не разрешается:**

Артефакт называется `cache-redis-lettuce`. `cache-redis-common` содержит только контракты и подтягивается транзитивно.

**Подключение к Redis падает на старте:**

Проверьте, что Redis запущен и что `lettuce.uri` указывает на достижимый экземпляр:

```bash
docker compose ps
docker compose logs redis
```

**Старт падает из-за отсутствующего `keyPrefix`:**

У `keyPrefix` нет значения по умолчанию в секции кеша Redis. Каждый блок `cache.redis.*` обязан его задать.

**Значения попадают в Redis, но чтения все равно промахиваются:**

Сравните `args` в `@CachePut` с параметрами, используемыми в `@Cacheable`. Если запись включает параметр, которого нет в чтении, они дают разные ключи и никогда не встретятся.

**Gradle зависает или неожиданно падает:**

Остановите демоны Gradle и повторите:

```bash
./gradlew --stop
./gradlew clean classes
```

**Windows `AccessDeniedException` в кеше Gradle:**

Если Windows держит открытыми файловые дескрипторы в `.gradle` или `build/`, остановите демоны Gradle, закройте процессы IDE, которые все еще следят за каталогом, и повторите команду.

**Тесты Redis на Testcontainers падают:**

Убедитесь, что Docker запущен и доступен из текущей оболочки. Тесты приложения-компаньона используют Testcontainers с Redis и подставляют `REDIS_URL` динамически.

**Проблемы с контекстом сборки или compose в Docker:**

Если `docker compose` не находит файл или стартует не оттуда, запускайте его из каталога модуля приложения, где лежит `docker-compose.yml`.

**Проверки готовности падают на последующих шагах наблюдаемости:**

Если вы продолжите это приложение наблюдаемостью, помните, что системный управляющий API использует порт `8085`, а готовность проверяется по `/system/readiness`.

## Что дальше? { #whats-next }

- [Шаблоны отказоустойчивости](resilient.md), чтобы защитить вызовы до того, как они наполнят локальный и распределенный кеши.
- [Наблюдаемость](observability.md), чтобы следить за попаданиями в кеш, вызовами Redis, задержками и сбоями.
- [База данных JDBC](database-jdbc.md), если перед сквозным черноящичным тестированием нужно приложение с настоящим хранением.
- [Обмен сообщениями с Kafka](messaging-kafka.md), когда закешированным моделям чтения нужно реагировать на события.

## Помощь { #help }

Если возникнут сложности:

- сравните с [Kora Java Cache Multi Level App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-cache-multi-level-app) и [Kora Kotlin Cache Multi Level App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-cache-multi-level-app)
- посмотрите [документацию по кешу](../documentation/cache.md)
- посмотрите [пример кеша Redis](https://github.com/kora-projects/kora-examples/tree/master/examples/java/kora-java-cache-redis)
- перечитайте [Стратегии кеширования](cache.md) для базовой линии одноуровневого кеша
