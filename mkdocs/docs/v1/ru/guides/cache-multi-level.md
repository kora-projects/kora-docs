---
search:
  exclude: true
title: Многоуровневое кеширование с Redis
summary: Learn how to extend the Caffeine cache guide with Redis as a shared second-level cache for Kora applications
tags: caching, redis, caffeine, multi-level, distributed, performance
---

# Многоуровневое кеширование с Redis { #multi-level-caching-redis }

Это руководство знакомит с многоуровневым кешированием в Kora, Caffeine и Redis. В нем рассматривается, как быстрый локальный кеш L1 и общий кеш Redis L2 работают вместе, как Kora объединяет
реализации кеша за одним кеш-договором, и как аннотации кеширования на уровне службы сохраняют чтения и инвалидацию согласованными. Вы также увидите, почему Redis рассматривается как общая
кеш-инфраструктура, а не как источник истины.

===! ":fontawesome-brands-java: `Java`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Java Cache Multi Level App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-cache-multi-level-app).

=== ":simple-kotlin: `Kotlin`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Kotlin Cache Multi Level App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-cache-multi-level-app).

## Что вы создадите { #youll-build }

В этом руководстве вы превратите одноуровневый кеш из предыдущего руководства в двухуровневый кеш, где:

- `UserCaffeineCache` остается быстрым локальным кешем L1
- `UserRedisCache` становится общим кешем L2
- `getUser()` сначала проверяет Caffeine, затем Redis, затем репозиторий
- `createUser()` сразу прогревает оба уровня кеша
- `updateUser()` обновляет оба уровня кеша
- `deleteUser()` вытесняет устаревшие данные из обоих уровней кеша
- HTTP API `/users` остается неизменным, а поведение кеша становится удобным для нескольких экземпляров приложения

## Что понадобится { #youll-need }

- JDK 17 или новее
- Gradle 7+
- текстовый редактор или среда разработки
- Docker или другая локальная среда выполнения Redis
- пройденное руководство [Стратегии кеширования с Kora](cache.md)

## Требования { #prerequisites }

!!! note "Обязательно: пройдите руководство по кешированию"

    Это руководство предполагает, что вы уже прошли **[Стратегии кеширования с Kora](cache.md)** и у вас уже есть те же `Application`, `UserController`, `UserService`, DTO и договор `UserCaffeineCache` из того руководства.

    Если вы еще не прошли руководство по кешированию, сначала сделайте это, потому что здесь сохраняется тот же API `/users` и добавляется Redis как второй слой кеша.

## Обзор { #overview }

В предыдущем руководстве использовался только **локальный кеш в памяти**. Это хорошо работает, когда приложение запущено в одной JVM, потому что каждое повторное чтение можно обслужить из локальной
памяти.

Но когда приложение запускается в нескольких подах или нескольких экземплярах, одного локального кеша для некоторых нагрузок уже недостаточно:

- у каждого пода свое содержимое кеша
- значение, прогретое в поде A, не становится автоматически видимым в поде B
- обновление, обработанное подом A, не обновляет локальную память пода B
- после перезапуска под снова начинает с пустым локальным кешем

Поэтому распространенный следующий шаг - **многоуровневое кеширование**.

В этом руководстве мы используем два слоя:

1. **L1: Caffeine**
   Это тот же локальный кеш в памяти из предыдущего руководства. Это самый быстрый слой, идеально подходящий для горячих повторных чтений внутри одного процесса.
2. **L2: Redis**
   Это общий распределенный кеш. Он медленнее локальной памяти, но все равно гораздо быстрее, чем каждый раз обращаться к первичному источнику.

Типичный процесс чтения теперь выглядит так:

1. Сначала попробовать Caffeine.
2. Если в Caffeine промах, попробовать Redis.
3. Если в Redis тоже промах, загрузить из репозитория.
4. Сохранить значение обратно в кеш, чтобы последующие чтения были дешевле.

Такая слоистая модель полезна, потому что уравновешивает скорость и совместное использование:

- Caffeine дает минимальную задержку для горячих значений внутри одного пода.
- Redis позволяет разным подам переиспользовать одно и то же кешированное значение.
- Репозиторий остается источником истины, когда в обоих кешах промах.

### Redis как L2-кеш { #redis-l2 }

Redis часто используют как кеш второго уровня, потому что он предоставляет:

- доступ в памяти с низкой задержкой
- общее состояние между экземплярами
- истечение срока действия ключей и префиксы ключей
- зрелые эксплуатационные инструменты
- простое развертывание для локальной разработки и промышленной среды

В этом руководстве Redis не рассматривается как источник истины. Это по-прежнему кеш. Репозиторий остается авторитетным источником, а Redis лишь помогает разным экземплярам приложения не повторять
одни и те же обращения.

### Модель кеша Kora { #cache-model }

Полная модель композитного кеша описана в разделе [композитного кеша](../documentation/cache.md#composite-cache), а Redis-уровень — в разделе [Redis](../documentation/cache.md#redis).

Поддержка кеша в Kora хорошо подходит для слоистых кешей, потому что кеш-договоры типизированы, а аннотации кеширования можно сочетать.

Это значит, что можно определить два отдельных кеш-интерфейса:

- `UserCaffeineCache extends CaffeineCache<String, UserResponse>`
- `UserRedisCache extends RedisCache<String, @Json UserResponse>`

Затем можно разместить несколько аннотаций на одном методе службы:

- `@Cacheable(UserCaffeineCache.class)`
- `@Cacheable(UserRedisCache.class)`

Kora применяет их в порядке объявления, сверху вниз. Поэтому на практике:

- сначала проверяется L1 Caffeine
- затем L2 Redis
- затем выполняется исходный метод, если в обоих кешах промах

Та же идея применима к `@CachePut` и `@CacheInvalidate`.

## Зависимости { #dependencies }

Добавьте кеширование Redis в существующее приложение руководства по кешированию.

===! ":fontawesome-brands-java: `Gradle Groovy`"

    Обновите `guides/guide-cache-multi-level-app/build.gradle`:

    ```groovy
    dependencies {
        implementation "ru.tinkoff.kora:cache-redis"
    }
    ```

=== ":simple-kotlin: `Gradle Kotlin DSL`"

    Обновите `build.gradle.kts`:

    ```kotlin
    dependencies {
        implementation("ru.tinkoff.kora:cache-redis")
    }
    ```

## Модули { #modules }

Базовое руководство по кешированию уже включает `CaffeineCacheModule`. Для многоуровневого кеша графу приложения также нужен `RedisCacheModule`.

===! ":fontawesome-brands-java: `Java`"

    Обновите `guides/guide-cache-multi-level-app/src/main/java/ru/tinkoff/kora/guide/cache/Application.java`:

    ```java
    package ru.tinkoff.kora.guide.cache;

    import ru.tinkoff.kora.application.graph.KoraApplication;
    import ru.tinkoff.kora.cache.caffeine.CaffeineCacheModule;
    import ru.tinkoff.kora.cache.redis.RedisCacheModule;
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
            CaffeineCacheModule,  // <----- Подключили модуль
            RedisCacheModule {  // <----- Подключили модуль

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
    import ru.tinkoff.kora.cache.redis.RedisCacheModule
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
        CaffeineCacheModule,  // <----- Подключили модуль
        RedisCacheModule  // <----- Подключили модуль

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

## Многоуровневый кеш контракт { #cache-contract }

Подробнее о Redis-кешах, сериализации значений и типизированных контрактах смотрите в [Redis-разделе документации кеша](../documentation/cache.md#redis).

Предыдущее руководство уже определило `UserCaffeineCache`. Теперь мы добавляем второй договор для Redis.

Этот договор важен по двум причинам:

- аннотации могут ссылаться на него декларативно
- тот же кеш можно внедрять напрямую, когда нужен ручной контроль

Кеш Caffeine хранит Java-объекты напрямую в локальной памяти, поэтому он может держать `UserResponse` как есть. Redis устроен иначе: значения должны сериализоваться перед записью в Redis и
десериализоваться при чтении обратно.

Чтобы этот шаблон чисто работал с Kora:

- оставьте `@Json` на DTO, чтобы Kora знала, как сериализовать и десериализовать полезную нагрузку
- пометьте тип значения Redis-кеша как `@Json UserResponse`, чтобы кеш-договор явно говорил, какой сериализованный тип хранит Redis

`@Json` здесь также говорит Kora, что значение должно использовать сериализатор и десериализатор, квалифицированные тегом `@Json`. Для Redis-кешей модуль Redis предоставляет такой тегированный
преобразователь из коробки, поэтому это работает без дополнительного ручного связывания.

Та же идея гибкая: при желании можно использовать другой тег для ключа или типа значения, если в графе есть соответствующий преобразователь с этим тегом.

Это делает договор самоописательным и позволяет Kora автоматически разрешить правильный преобразователь вместо отдельного ручного преобразователя значения Redis.

В рабочем приложении Redis хранит `UserResponse`, поэтому договор использует `String` как ключ и `@Json UserResponse` как тип значения.

===! ":fontawesome-brands-java: `Java`"

    Создайте `guides/guide-cache-multi-level-app/src/main/java/ru/tinkoff/kora/guide/cache/service/UserRedisCache.java`:

    ```java
    package ru.tinkoff.kora.guide.cache.service;

    import ru.tinkoff.kora.cache.annotation.Cache;
    import ru.tinkoff.kora.cache.redis.RedisCache;
    import ru.tinkoff.kora.guide.cache.dto.UserResponse;
    import ru.tinkoff.kora.json.common.annotation.Json;

    @Cache("cache.redis.users")
    public interface UserRedisCache extends RedisCache<String, @Json UserResponse> {
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Создайте `src/main/kotlin/ru/tinkoff/kora/guide/cache/service/UserRedisCache.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.cache.service

    import ru.tinkoff.kora.cache.annotation.Cache
    import ru.tinkoff.kora.cache.redis.RedisCache
    import ru.tinkoff.kora.guide.cache.dto.UserResponse
    import ru.tinkoff.kora.json.common.annotation.Json

    @Cache("cache.redis.users")
    interface UserRedisCache : RedisCache<String, @Json UserResponse>
    ```

## Многоуровневый кеш реализация { #cache-impl }

Служба продолжает ту, что была в руководстве по кешированию. Неизмененные части ведут себя так же:

- `getUsers()` по-прежнему применяет сортировку и постраничную выдачу
- вспомогательный компаратор остается тем же
- HTTP-поведение `404` по-прежнему находится в службе

Здесь мы показываем только методы, которые меняются для многоуровневого кеширования:

- `getUser()` - `@Cacheable` объявлена дважды, поэтому Kora сначала проверяет Caffeine, а затем Redis.
- `updateUser()` - `@CachePut` объявлена дважды, поэтому оба слоя обновляются после успешного обновления.
- `deleteUser()` - `@CacheInvalidate` объявлена дважды, поэтому оба слоя вытесняют устаревшее значение.

===! ":fontawesome-brands-java: `Java`"

    Обновите измененные методы в `guides/guide-cache-multi-level-app/src/main/java/ru/tinkoff/kora/guide/cache/service/UserService.java`:

    ```java
    @Cacheable(UserCaffeineCache.class)
    @Cacheable(UserRedisCache.class)
    public Optional<UserResponse> getUser(String id) {
        return userRepository.findById(id);
    }

    @CachePut(value = UserCaffeineCache.class, parameters = { "id" })
    @CachePut(value = UserRedisCache.class, parameters = { "id" })
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

    Обновите измененные методы в `src/main/kotlin/ru/tinkoff/kora/guide/cache/service/UserService.kt`:

    ```kotlin
    @Cacheable(UserCaffeineCache::class)
    @Cacheable(UserRedisCache::class)
    open fun getUser(id: String): UserResponse? {
        return userRepository.findById(id).orElse(null)
    }

    @CachePut(value = UserCaffeineCache::class, parameters = ["id"])
    @CachePut(value = UserRedisCache::class, parameters = ["id"])
    open fun updateUser(id: String, request: UserRequest): UserResponse {
        val updated = userRepository.update(id, request.name, request.email)
        if (!updated) {
            throw HttpServerResponseException.of(404, "User not found")
        }
        return UserResponse(id, request.name, request.email, LocalDateTime.now())
    }

    @CacheInvalidate(UserCaffeineCache::class)
    @CacheInvalidate(UserRedisCache::class)
    open fun deleteUser(id: String) {
        val deleted = userRepository.deleteById(id)
        if (!deleted) {
            throw HttpServerResponseException.of(404, "User not found")
        }
    }
    ```

В окружении с N подами это значительно меняет поведение по сравнению с только локальным кешированием:

- промах в одном поде все равно может стать попаданием в Redis
- повторные чтения в том же поде по-прежнему получают пользу от скорости локального Caffeine
- обновления и удаления теперь обновляют или вытесняют общий уровень кеша, а не только память одного пода

## Прогрейв кеша { #cache-warmup }

`createUser()` все еще требует ручного управления кешем, потому что идентификатор пользователя сначала генерируется репозиторием.

Это один из самых понятных примеров того, почему типизированные кеш-договоры полезны: те же кеши, которые используются аннотациями, можно внедрять и контролировать напрямую.

===! ":fontawesome-brands-java: `Java`"

    Обновите путь создания в `guides/guide-cache-multi-level-app/src/main/java/ru/tinkoff/kora/guide/cache/service/UserService.java`:

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

    Обновите путь создания в `src/main/kotlin/ru/tinkoff/kora/guide/cache/service/UserService.kt`:

    ```kotlin
    fun createUser(request: UserRequest): UserResponse {
        val generatedId = userRepository.save(request.name, request.email)
        val createdUser = UserResponse(generatedId, request.name, request.email, LocalDateTime.now())
        userCaffeineCache.put(createdUser.id, createdUser)
        userRedisCache.put(createdUser.id, createdUser)
        return createdUser
    }
    ```

Так следующее чтение может сразу обслужиться из кеша, а Redis уже содержит новую сущность и для других экземпляров.

## Конфигурация { #config }

Оставьте настройку HTTP-сервера из предыдущего руководства как есть. В этом руководстве обновите только конфигурацию кеша и Redis-клиента.

Обновите `guides/guide-cache-multi-level-app/src/main/resources/application.conf`:

Полный справочник по конфигурации смотрите в разделе [Кеш](../documentation/cache.md).

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

    1. Максимальное число записей кеша перед началом вытеснения.
    2. Время, через которое запись Caffeine истекает после записи.
    3. Префикс, добавляемый к ключам, которые хранятся в Redis.
    4. Время, через которое запись Redis истекает после записи.
    5. URI подключения к локальному Redis по умолчанию.
    6. URI подключения. Необязательное переопределение из `REDIS_URL`.
    7. Имя пользователя, которое используется клиентским подключением. Необязательное переопределение из `REDIS_USER`.
    8. Пароль пользователя базы данных. Необязательное переопределение из `REDIS_PASS`.
    9. Тайм-аут операции сокета.
    10. Тайм-аут выполнения команды Redis.

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

    1. Максимальное число записей кеша перед началом вытеснения.
    2. Время, через которое запись Caffeine истекает после записи.
    3. Префикс, добавляемый к ключам, которые хранятся в Redis.
    4. Время, через которое запись Redis истекает после записи.
    5. URI подключения с локальным значением по умолчанию и необязательным переопределением из `REDIS_URL`.
    6. Имя пользователя, которое используется клиентским подключением. Необязательное переопределение из `REDIS_USER`.
    7. Пароль пользователя базы данных. Необязательное переопределение из `REDIS_PASS`.
    8. Тайм-аут операции сокета.
    9. Тайм-аут выполнения команды Redis.

Здесь важны несколько деталей:

- `cache.caffeine.users` соответствует `UserCaffeineCache`
- `cache.redis.users` соответствует `UserRedisCache`
- `keyPrefix` предотвращает пересечения внутри Redis
- `REDIS_URL` позволяет тестам или другим окружениям переопределить локальный URI по умолчанию

## Docker Compose { #docker-compose }

Для локальных запусков руководства самый простой вариант - небольшой файл Docker Compose.

Создайте `docker-compose.yml` в каталоге модуля приложения:

```yaml
services:
  redis:
    image: redis:8.2-alpine
    ports:
      - "6379:6379"
    command: redis-server --save 60 1 --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
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

Используйте стандартный процесс запуска:

```bash
./gradlew clean classes
./gradlew test
./gradlew run
```

Рабочий сопутствующий модуль также проверяет многоуровневое поведение сфокусированными компонентными тестами с Redis.

## Проверка приложения { #check-app }

Сначала создайте пользователя:

```bash
curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -d '{"name":"John Doe","email":"john@example.com"}'
```

Прочитайте того же пользователя дважды. Второй запрос должен обслуживаться из кеша, а в настоящем развертывании с несколькими экземплярами Redis дает общий запасной слой, когда у другого экземпляра
промах в локальном Caffeine.

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

Если после этого хотите остановить локальный Redis:

```bash
docker compose down
```

## Лучшие практики { #best-practices }

- Оставляйте Caffeine первым слоем кеша для горячих чтений внутри процесса.
- Используйте Redis как общий слой кеша, а не как замену источника истины.
- Делайте кеш-договоры типизированными и явными, чтобы их можно было использовать и декларативно, и императивно.
- Ставьте `@Json` на тип значения Redis, когда кешируете пользовательские DTO.
- Держите семантику обновления кеша рядом с бизнес-операциями: обновляйте при изменении, вытесняйте при удалении, явно прогревайте при создании.

## Итоги { #summary }

Вы расширили руководство по одноуровневому кешу до многоуровневой кеш-архитектуры.

Получившееся приложение теперь использует:

- локальный `UserCaffeineCache` для сверхбыстрых повторных чтений внутри одного экземпляра
- общий `UserRedisCache` для переиспользования между экземплярами
- слоистые чтения `@Cacheable`
- слоистые обновления `@CachePut`
- слоистые вытеснения `@CacheInvalidate`
- ручной прогрев двух кешей в `createUser()`

## Ключевые понятия { #key-concepts }

- многоуровневое кеширование объединяет преимущества локальной задержки и общего распределенного переиспользования
- Caffeine и Redis решают разные задачи и хорошо работают вместе
- Kora применяет несколько аннотаций кеширования в порядке объявления
- значения Redis-кеша для пользовательских DTO требуют явного JSON-осознанного типа
- типизированные кеш-договоры можно внедрять напрямую для ручного управления кешем

## Устранение неполадок { #troubleshooting }

**Сборка графа падает для `RedisCacheValueMapper<...>`:**

Если вы кешируете пользовательский DTO в Redis, убедитесь, что договор Redis-кеша использует `@Json` на типе значения, например:

```java
public interface UserRedisCache extends RedisCache<String, @Json UserResponse> {
}
```

Без этого Kora может не сгенерировать преобразователь значения Redis для вашего DTO.

**Подключение к Redis падает при запуске:**

Проверьте, что Redis запущен и `lettuce.uri` указывает на доступный экземпляр:

```bash
docker compose ps
docker compose logs redis
```

**Gradle зависает или неожиданно падает:**

Остановите демоны Gradle и повторите:

```bash
./gradlew --stop
./gradlew clean classes
```

**Windows `AccessDeniedException` в кеше Gradle:**

Если Windows держит открытые файловые дескрипторы в `.gradle` или `build/`, остановите демоны Gradle, закройте процессы среда разработки, которые все еще наблюдают за каталогом, и повторите команду.

**Тесты Redis на основе Testcontainers падают:**

Убедитесь, что Docker запущен и доступен из текущей оболочки. Тесты сопутствующего приложения используют Redis Testcontainers и динамически внедряют `REDIS_URL`.

**Проблемы сборки Docker или контекста compose:**

Если `docker compose` не может найти файл или запускается из неправильного места, выполняйте его из каталога модуля приложения, где находится `docker-compose.yml`.

**Проверки готовности падают в последующих шагах наблюдаемости:**

Если продолжаете это приложение с наблюдаемостью, помните, что закрытый управляющий API использует порт `8085`, а готовность проверяется по `/system/readiness`.

## Что дальше? { #whats-next }

- [Шаблоны устойчивости](resilient.md), чтобы защитить вызовы до того, как они заполнят локальный и распределенный кеш.
- [Наблюдаемость](observability.md), чтобы наблюдать за попаданиями в кеш, вызовами Redis, задержкой и сбоями.
- [База данных JDBC](database-jdbc.md), если хотите приложение с постоянным хранилищем перед сквозным тестированием как черный ящик.
- [Сообщения с Kafka](messaging-kafka.md), когда кешированные модели чтения должны реагировать на события.

## Помощь { #help }

Если столкнулись с проблемой:

- сравните с [Kora Java Cache Multi Level App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-cache-multi-level-app) и [Kora Kotlin Cache Multi Level App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-cache-multi-level-app)
- проверьте [документацию кеша](../documentation/cache.md)
- проверьте [пример Redis-кеша](https://github.com/kora-projects/kora-examples/tree/master/kora-java-cache-redis)
- вернитесь к [Стратегиям кеширования](cache.md) за базой одноуровневого кеша
