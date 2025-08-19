Модуль для создания кешей на основе [Caffeine](https://github.com/ben-manes/caffeine) или [Redis](https://redis.io/docs/about/)
с помощью аннотаций в декларативном стиле, так и использование их императивном стиле.

## Caffeine

Реализация на основе библиотеки [Caffeine](https://github.com/ben-manes/caffeine) для кэша внутри памяти приложения.

### Подключение

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#_4) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:cache-caffeine"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends CaffeineCacheModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#_4) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:cache-caffeine")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : CaffeineCacheModule
    ```

### Конфигурация

Пример полной конфигурации для `mycache.config` кэша, параметры описаны в классе `CaffeineCacheConfig` (указаны примеры значений или значения по умолчанию):

===! ":material-code-json: `Hocon`"

    ```javascript
    mycache {
        config {
            expireAfterWrite = "10s" //(1)!
            expireAfterAccess = "10s" //(2)!
            initialSize = 10 //(3)!
            maximumSize = 100000 //(4)!
        }
    }
    ```

    1.  Время по истечении которого значение для ключа будет удалено, отчитывается после добавления значения (необязательно)
    2.  Время по истечении которого значение для ключа будет удалено, отчитывается после операции чтения (необязательно)
    3.  Начальный размер кэша (помогает избежать расширения кэша в случае активного набухания) (необязательно)
    4.  Максимальный размер кэша (При достижении границы **или чуть ранее** будет исключать из кэша [наименее актуальные значения](https://blog.skillfactory.ru/glossary/lru/)) (по умолчанию `100000`)

=== ":simple-yaml: `YAML`"

    ```yaml
    mycache:
      config:
        expireAfterWrite: "10s" #(1)!
        expireAfterAccess: "10s" #(2)!
        initialSize: 10 #(3)!
        maximumSize: 100000 #(4)!
    ```

    1.  Время по истечении которого значение для ключа будет удалено, отчитывается после добавления значения (необязательно)
    2.  Время по истечении которого значение для ключа будет удалено, отчитывается после операции чтения (необязательно)
    3.  Начальный размер кэша (помогает избежать расширения кэша в случае активного набухания) (необязательно)
    4.  Максимальный размер кэша (При достижении границы **или чуть ранее** будет исключать из кэша [наименее актуальные значения](https://blog.skillfactory.ru/glossary/lru/)) (по умолчанию `100000`)

## Redis

Реализация на основе базы данных в памяти [Redis](https://redis.io/docs/about/) и драйвера подключения [Lettuce](https://github.com/lettuce-io/lettuce-core).

### Подключение

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#_4) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:cache-redis"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends RedisCacheModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#_4) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:cache-redis")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : RedisCacheModule
    ```

### Конфигурация

Требуется отдельно сконфигурировать Lettuce драйвер для подключения к Redis.
Используется одно подключение для всех кешей.

Пример полной конфигурации для *lettuce* драйвера, параметры описаны в классе `LettuceConfig` (указаны примеры значений или значения по умолчанию):

===! ":material-code-json: `Hocon`"

    ```javascript
    lettuce {
        uri = "redis://locahost:6379" //(1)!
        user = "admin" //(2)!
        password = "12345" //(3)!
        database = 0 //(4)!
        protocol = "REP3" //(5)!
        socketTimeout = "10s" //(6)!
        commandTimeout = "60s" //(7)!
        ssl {
            ciphers = [ "TLS_CHACHA20_POLY1305_SHA256" ] //(8)!
            handshakeTimeout = "10s" //(9)!
        } 
    }
    ```

    1.  URI для подключения к Redis (**обязательный**)
        Подключение для 1 сервера: `redis://locahost:6379`,
        Подключение для N серверов: `redis://locahost:6379,locahost:6380`, 
        Подключение для c SSL: `rediss://locahost:6380`
        Подключение для c TLS: `redis+tls://locahost:6380`
    2.  Имя пользователя для подключения (необязательно)
    3.  Пароль пользователя для подключения (необязательно)
    4.  Номер базы для подключения (необязательно)
    5.  Протокол для подключения (необязательно)
    6.  Таймаут времени подключения (необязательно)
    7.  Таймаут времени выполнения команды (необязательно)
    8.  Алгоритмы шифрования, используемые для безопасного соединения между клиентом и сервером (необязательно)
    9.  Таймаут времени установки безопасного соединения с сервером (необязательно)

=== ":simple-yaml: `YAML`"

    ```yaml
    lettuce:
      uri: "redis://locahost:6379" #(1)!
      user: "admin" #(2)!
      password: "12345" #(3)!
      database: 0 #(4)!
      protocol: "REP3" #(5)!
      socketTimeout: "10s" #(6)!
      commandTimeout: "60s" #(7)!
      ssl:
        ciphers:
          - "TLS_CHACHA20_POLY1305_SHA256" #(8)!
        handshakeTimeout: "10s" #(9)!
    ```

    1.  URI для подключения к Redis (**обязательный**)
        Подключение для 1 сервера: `redis://locahost:6379`,
        Подключение для N серверов: `redis://locahost:6379,locahost:6380`, 
        Подключение для c SSL: `rediss://locahost:6380`
        Подключение для c TLS: `redis+tls://locahost:6380`
    2.  Имя пользователя для подключения (необязательно)
    3.  Пароль пользователя для подключения (необязательно)
    4.  Номер базы для подключения (необязательно)
    5.  Протокол для подключения (необязательно)
    6.  Таймаут времени подключения (необязательно)
    7.  Таймаут времени выполнения команды (необязательно)
    8.  Алгоритмы шифрования, используемые для безопасного соединения между клиентом и сервером (необязательно)
    9.  Таймаут времени установки безопасного соединения с сервером (необязательно)

Конфигурации Redis кэша настраивает именно поведение конкретного кэша.

Пример полной конфигурации для `mycache.config` кэша, параметры описаны в классе `RedisCacheConfig` (указаны примеры значений):

===! ":material-code-json: `Hocon`"

    ```javascript
    mycache {
        config {    
            expireAfterWrite = "10s" //(1)!
            expireAfterAccess = "10s" //(2)!
            keyPrefix = "mykey" //(3)!
        }
    }
    ```

    1.  При записи устанавливает время [expiration](https://redis.io/commands/psetex/)
    2.  При чтении устанавливает время [expiration](https://redis.io/commands/getex/)
    3.  Префикс ключа в определенном кеше для избежания коллизий ключе в рамках Redis базы данных, может быть пустой строкой тогда ключи будут без префикса (**обязательный**)

=== ":simple-yaml: `YAML`"

    ```yaml
    mycache:
      config:
        expireAfterWrite: "10s" #(1)!
        expireAfterAccess: "10s" #(2)!
        keyPrefix: "mykey" //(3)!
    ```

    1.  При записи устанавливает время [expiration](https://redis.io/commands/psetex/)
    2.  При чтении устанавливает время [expiration](https://redis.io/commands/getex/)
    3.  Префикс ключа в определенном кеше для избежания коллизий ключе в рамках Redis базы данных, может быть пустой строкой тогда ключи будут без префикса (**обязательный**)

#### Донастройка

Можно зарегистрировать `LettuceConfigurator` который позволит до настроить `Lettuce` клиент перед созданием.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class MyLettuceConfigurator implements LettuceConfigurator {
        @Override
        public DefaultClientResources.Builder configure(DefaultClientResources.Builder resouceBuilder) {
            return resouceBuilder;
        }

        @Override
        public ClusterClientOptions.Builder configure(ClusterClientOptions.Builder clusterBuilder) {
            return clusterBuilder;
        }

        @Override
        public ClientOptions.Builder configure(ClientOptions.Builder clientBuilder) {
            return clientBuilder;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class MyLettuceConfigurator : LettuceConfigurator {

        override fun configure(resouceBuilder: DefaultClientResources.Builder): DefaultClientResources.Builder {
            return resouceBuilder
        }

        override fun configure(clusterBuilder: ClusterClientOptions.Builder): ClusterClientOptions.Builder {
            return clusterBuilder
        }

        override fun configure(clientBuilder: ClientOptions.Builder): ClientOptions.Builder {
            return clientBuilder
        }
    }
    ```

## Использование

Для создания кеша потребуется зарегистрировать типизированный `@Cache` контракт.
Интерфейс контракта должен наследоваться только от предоставляемых Kora'ой реализаций: `CaffeineCache` / `RedisCache`.
Для такого `@Cache` будет создана и добавлена в граф реализация, ее можно будет использовать для внедрения зависимостей.

Для регистрации `@Cache` и указания конфига требуется проаннотировать аннотацией `@Cache` где аргумент `value` означает полный путь к конфига.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Cache("mycache.config")
    public interface MyCache extends CaffeineCache<String, String> { }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Cache("mycache.config")
    interface MyCache : CaffeineCache<String, String>
    ```

### Императивный подход

Кеши доступны для внедрения как зависимости по интерфейсу и могут использовать вкупе с декларативными операциями.

Реализация `CaffeineCache` предоставляет базовые контракты интерфейса `Cache` для синхронных операций,
а `RedisCache` предоставляет как `Cache` так и `AsyncCache` для асинхронных операций с `CompletionStage` сигнатурами.

Интерфейсы предоставляют операции получения, удаления, обновления, пакетных операций и тп.
Также реализации кешей могут предоставлять специфичные для себя контракты.

### Декларативный подход

Все примеры использования аспектов будут подразумевать реализацию кэша выше.

#### Получение

Для кэширования и получения значения из кэша для метода *get()* следует проаннотировать его аннотацией `@Cacheable`.

Ключ для кэша составляет из аргументов метода, порядок аргументов имеет значение, в данном случае он будет составляться из значения `arg1`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @Cacheable(MyCache.class)
        public String get(String arg1) {
            // do something
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService {

        @Cacheable(MyCache::class)
        fun get(arg1: String): String {
            // do something
        }
    }
    ```

#### Сохранение

Для добавления значений в кэш через метод *put()* следует проаннотировать его аннотацией `@CachePut`.
Метод проаннотированный `@CachePut` будет вызван и его значение положено в кэш определенный в *value*.

Ключ для кэша составляет из аргументов метода, порядок аргументов имеет значение, в данном случае он будет составляться из значения `arg1`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @CachePut(MyCache.class)
        public String put(String arg1) {
            // do something
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService {

        @CachePut(MyCache::class)
        fun put(arg1: String): String {
            // do something
        }
    }
    ```

#### Удаление

Для удаления значения по ключу из кэша через метод *evict()* следует проаннотировать его аннотацией `@CacheInvalidate`.
Метод проаннотированный `@CacheInvalidate` будет вызван и затем по ключу для кэша определенного в *value* будут удалены значения по ключу.

Ключ для кэша составляет из аргументов метода, порядок аргументов имеет значение, в данном случае он будет составляться из значения `arg1`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @CacheInvalidate(MyCache.class)
        public void evict(String arg1) {
            // do something
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService {

        @CacheInvalidate(MyCache::class)
        fun evict(arg1: String) {
            // do something
        }
    }
    ```

#### Полное удаление

Для удаления всех значений из кэша через метод *evictAll()* следует проаннотировать его аннотацией `@CacheInvalidate` и указать параметр *invalidateAll = true*.

Метод проаннотированный `@CacheInvalidate` будет вызван и затем будут удалены все из кэша определенного в *value*.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @CacheInvalidate(value = MyCache.class, invalidateAll = true)
        public void evictAll(String arg1) {
            // do something
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService {

        @CacheInvalidate(value = MyCache::class, invalidateAll = true)
        fun evict(arg1: String) {
            // do something
        }
    }
    ```

#### Композитный кэш

В случае если у вас есть несколько кешей то требуется подключить оба модуля и указать соответствующее количество аннотаций над методом.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends RedisCacheModule, CaffeineCacheModule {

        @Cache("mycache.caffeine.config")
        public interface MyCaffeineCache extends CaffeineCache<String, String> { }

        @Cache("mycache.redis.config")
        public interface MyRedisCache extends RedisCache<String, String> { }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application : RedisCacheModule, CaffeineCacheModule { 

        @Cache("mycache.caffeine.config")
        interface MyCaffeineCache : CaffeineCache<String, String> { }

        @Cache("mycache.redis.config")
        interface MyRedisCache : RedisCache<String, String> { }
    }
    ```

А сам проаннотированный класс так:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @Cacheable(MyCaffeineCache.class)
        @Cacheable(MyRedisCache.class)
        public String get(String arg1) {
            // do something
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService {

        @Cacheable(MyCaffeineCache::class)
        @Cacheable(MyRedisCache::class)
        fun get(arg1: String): String {
            // do something
        }
    }
    ```

Порядок вызова аспектов соответствует порядку аннотаций над методом, сверху внизу.

## Ключ

В случае если ключ кэша представляет собой 1 аргумент, то требуется зарегистрировать `Cache` с сигнатурой соответствующей типам ключа и значения.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Cache("mycache.config")
    public interface MyCache extends CaffeineCache<String, String> { }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Cache("mycache.config")
    interface MyCache : CaffeineCache<String, String>
    ```

### Преобразование

В случае если аргумент не может быть преобразован в ключ кеша, то реализация кеша затребует соответствующий преобразователь
с интерфейсом `CacheKeyMapper`, в случае если аргументов для ключа будет 2 то потребуется `CacheKeyMapper2` и так далее.

Такой преобразователь можно также предоставить в ручную с помощью аннотации `@Mapping`,
пример преобразования сложного объекта в простой ключ кеша:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        public record UserContext(String userId, String traceId) { }

        public static final class UserContextMapping implements CacheKeyMapper<String, UserContext> {

            @Nonnull
            @Override
            public String map(UserContext arg) {
                return arg.userId();
            }
        }

        @Mapping(UserContextMapping.class)
        @Cacheable(MyCache.class)
        public String get(UserContext context) {
            // do something
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService {

        @Cacheable(MyCache::class)
        fun get(arg1: String, arg2: BigDecimal): String {
            // do something
        }
    }
    ```

### Композитный ключ

В случае если ключ кэша представляет собой N аргументов, то требуется зарегистрировать `Cache` с использованием 
собственного класса который бы описывал такой ключ.

Пример для `Cache` где композитный ключ состоит из 2 элементов:

===! ":fontawesome-brands-java: `Java`"
    
    Предполагается создавать собственный `record` класс который бы описывал композитный ключ.

    ```java
    @Cache("mycache.config")
    public interface MyCache extends CaffeineCache<MyCache.Key, String> {
        
        record Key(String k1, Long k2) { }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Предполагается создавать собственный `data` класс который бы описывал композитный ключ.

    ```kotlin
    @Cache("mycache.config")
    interface MyCache : CaffeineCache<MyCache.Key, String> {

        data class Key(val k1: String, val k2: Long)
    }
    ```

Если используется `RedisCache` то подразумевается что по умолчанию все аргументы композитного ключа будут не `null`, 
либо потребуется использовать собственный преобразователь ключа.

### Порядок аргументов

В случае если метод принимает аргументы которые хочется исключить из композитного ключа,
либо же порядок аргументов не соответствует порядку аргументов конструктора композитного ключа,
следует использовать атрибут аннотации `parameters` и определить какие именно аргументы метода использовать и в каком порядке.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @Cacheable(value = MyCache.class, parameters = {"arg1", "arg2"})
        public String get(Long arg2, String arg3, String arg1) {
            // do something
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService {

        @Cacheable(value = MyCache::class, parameters = ["arg1", "arg2"])
        fun get(arg2: Long, arg3: String, arg1: String): String {
            // do something
        }
    }
    ```

## Подгружаемый кэш

Библиотека предоставляет компонент для построения сущности, которая объединяет операции GET и PUT, без использования аспектов - `LoadableCache`

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Cache("mycache.config")
    public interface MyCache extends CaffeineCache<String, String> { }

    @KoraApp
    public interface Application : CaffeineCacheModule {

        default LoadableCache<String, String> loadableCache(MyCache cache, SomeService someService) {
            return cache.asLoadable(someService::loadEntity);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Cache("mycache.config")
    interface MyCache : CaffeineCache<String, String>

    @KoraApp
    interface Application : CaffeineCacheModule {

        fun loadableCache(
            cache: MyCache,
            someService: SomeService,
        ): LoadableCache<String, String> {
            return cache.asLoadable(someService::loadEntity)
        }
    }
    ```

## Сигнатуры

Доступные сигнатуры для методов которые поддерживают аннотации из коробки:

===! ":fontawesome-brands-java: `Java`"

    Класс не должен быть `final`, чтобы аспекты работали.

    Под `T` подразумевается тип возвращаемого значения.

    - `T myMethod()`
    - `Optional<T> myMethod()`
    - `CompletionStage<T> myMethod()` [CompletionStage](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/CompletionStage.html)
    - `Mono<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/) (надо подключить [зависимость](https://mvnrepository.com/artifact/io.projectreactor/reactor-core))

=== ":simple-kotlin: `Kotlin`"

    Класс должен быть `open`, чтобы аспекты работали.

    Под `T` подразумевается тип возвращаемого значения, либо `T?`, либо `Unit`.

    - `myMethod(): T`
    - `suspend myMethod(): T` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine) (надо подключить [зависимость](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) как `implementation`)
