---
search:
  exclude: true
title: Метрики с Kora
summary: Build focused Micrometer metrics for a Kora HTTP service, including framework metrics, business counters, timers, private metrics endpoints, and practical verification.
tags: observability, metrics, micrometer, meter-registry, counters, timers, monitoring
---

# Метрики с Kora { #observability-metrics-kora }

Это руководство фокусируется только на метриках. Вы возьмете приложение из руководства по HTTP-серверу и добавите к нему эксплуатационные и бизнес-метрики: приватный путь `/metrics`, модуль
Micrometer, собственный `MetricsService`, счетчик созданных пользователей и таймер операции создания.

===! ":fontawesome-brands-java: `Java`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Java Observability App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-observability-app).

=== ":simple-kotlin: `Kotlin`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Kotlin Observability App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-observability-app).

## Что вы создадите { #youll-build }

Вы добавите в HTTP-приложение:

- модуль `MetricsModule`
- приватный путь `/metrics` на управляющем порту
- пользовательский `MetricsService`
- таймер `user.creation.duration`
- счетчик `user.creation.total` с тегом `email.provider`
- проверку, что метрики появляются после вызова бизнес-операции

## Что понадобится { #youll-need }

- JDK 17 или новее
- Gradle 7+
- Docker, если хотите локально запустить проверку по принципу черного ящика
- текстовый редактор или среда разработки
- пройденное [руководство по HTTP-серверу](http-server.md)

## Требования { #prerequisites }

!!! note "Обязательная основа"

    Это руководство предполагает, что вы уже прошли **[руководство по HTTP-серверу](http-server.md)** и у вас уже есть HTTP-контроллеры, DTO, репозиторий, служба и конфигурация из того руководства.

    Если вы еще не прошли руководство по HTTP-серверу, сначала сделайте это, потому что это руководство по наблюдаемости сохраняет тот же HTTP-интерфейс и накладывает поверх него телеметрию.

## Обзор { #overview }

Метрики - это числа, которые приложение регулярно отдает наружу. Представьте табло рядом с сервисом: на нем видно, сколько запросов прошло, сколько пользователей создано, как долго выполнялись операции и сколько ресурсов сейчас занято. По одному числу обычно нельзя понять всю историю, но по набору чисел можно заметить, что приложение стало медленнее, начало чаще ошибаться или неожиданно выросло по нагрузке.

Kora как фреймворк уже поставляет основные системные и модульные метрики из коробки. Когда вы подключаете нужные модули, Kora сама отдает метрики для поддерживаемых частей приложения: HTTP-сервера, клиентов, баз данных, обмена сообщениями, инфраструктуры времени выполнения и других интеграций. Эти сигналы отдаются в стандартной для экосистемы наблюдаемости форме, совместимой с OpenTelemetry-подходом и системами мониторинга.

Самая важная идея: метрики нужны не только фреймворку и не только инфраструктуре. Фреймворк может посчитать технические вещи, например HTTP-запросы или показатели времени выполнения. Но только ваш код знает предметный смысл события. Kora не может сама догадаться, что вызов `createUser()` означает создание пользователя, поэтому бизнес-метрику нужно поставить в сервисном слое.

В этом руководстве используются три основные сущности:

- `MetricsModule` подключает поддержку метрик в граф Kora
- `MeterRegistry` является общей точкой, через которую приложение регистрирует свои метрики
- Micrometer предоставляет типы метрик, например `Counter` и `Timer`

Micrometer можно воспринимать как универсальный блокнот для чисел. Вы говорите ему: "вот счетчик с таким именем" или "вот таймер с таким именем", а дальше Micrometer хранит измерения в форме, которую могут читать системы мониторинга. Kora добавляет этот блокнот в граф приложения, чтобы компонент `MetricsService` мог получить `MeterRegistry` через конструктор.

### Модель сигнала { #signal-model }

Счетчик считает события. Он похож на механический счетчик на двери: каждый раз, когда событие произошло, значение увеличивается. В нашем случае `user.creation.total` увеличивается после успешного создания пользователя и получает тег `email.provider`, извлеченный из домена email. Такой счетчик помогает отвечать на вопросы:

- сколько созданий пользователей было за последние пять минут
- не прекратилась ли внезапно бизнес-активность
- не выросла ли частота операции после релиза
- какие email-провайдеры чаще всего встречаются у новых пользователей

Таймер измеряет длительность. Он похож на секундомер, который запускается вокруг операции и сохраняет не одно значение, а набор измерений. По таймеру можно смотреть среднее время, максимумы, перцентили и количество измерений. В нашем случае `user.creation.duration` показывает, сколько занимает создание пользователя.

Счетчик и таймер вместе дают более полезную картину, чем каждый по отдельности. Счетчик говорит "операция происходила", таймер говорит "операция занимала столько-то времени". Если счетчик растет, а таймер резко ухудшается, значит операция выполняется, но стала медленной. Если счетчик перестал расти, возможно, до этой операции вообще перестали доходить запросы.

### Инструменты { #tools }

`MetricsModule` - это Kora-модуль, который добавляет инфраструктуру метрик в приложение. После подключения модуль делает `MeterRegistry` доступным как обычную зависимость графа. Это важно: метрики не создаются вручную в `static`-поле и не передаются через глобальное состояние. Они живут в графе зависимостей так же, как репозиторий или HTTP-клиент.

`MeterRegistry` - это место регистрации. Когда `MetricsService` вызывает `Counter.builder(...).register(meterRegistry)`, он говорит: "создай или найди метрику с таким именем и описанием". После этого счетчик можно увеличивать, а таймер можно использовать для измерений.

Путь `/metrics` - это окно, через которое внешний мониторинг читает накопленные значения. В конфигурации руководства он находится на приватном порту `8085`. Это не случайность: метрики могут раскрывать внутреннее устройство сервиса, поэтому обычные пользователи не должны получать их через публичный API.

### Граница метрик { #metrics-boundary }

Хорошая бизнес-метрика ставится там, где есть бизнес-смысл. Для создания пользователя это `UserService`, а не HTTP-контроллер. Контроллер знает, что пришел HTTP-запрос. Сервис знает, что приложение действительно выполняет операцию создания.

В этом руководстве `MetricsService` оборачивает действие через `recordUserCreation()`. Такая форма удобна по трем причинам:

- имя метрики хранится в одном компоненте
- сервисный метод остается читаемым
- таймер измеряет ровно тот кусок работы, который передан в действие

Не нужно добавлять метрику на каждую строку кода. Метрики должны отвечать на вопросы, а не превращаться в шум. Если метрика не помогает принять решение, настроить оповещение или объяснить поведение сервиса, скорее всего, ее рано добавлять.

Еще один важный момент - теги. Теги полезны, когда нужно разделить измерения по стабильным категориям: статус операции, тип команды, имя клиента из небольшого фиксированного списка. Но теги опасны, если туда попадают идентификатор пользователя, полный email, исходный путь запроса или другие бесконечно разнообразные значения. Это называется высокой кардинальностью, и она быстро ломает хранение метрик.

Практический результат этой главы простой: сначала подключаем Kora-модуль, потом регистрируем понятные бизнес-метрики через `MeterRegistry`, затем проверяем их на приватном `/metrics`. Так метрики становятся частью приложения, а не отдельной магией мониторинга.

## Зависимости { #dependencies }

===! ":fontawesome-brands-java: `Java`"

    Добавьте Micrometer-модуль:

    ```groovy
    dependencies {
        // ... существующие зависимости из руководства по HTTP-серверу ...

        implementation("ru.tinkoff.kora:micrometer-module")
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Добавьте Micrometer-модуль:

    ```kotlin
    dependencies {
        // ... существующие зависимости из руководства по HTTP-серверу ...

        implementation("ru.tinkoff.kora:micrometer-module")
    }
    ```

## Модули { #modules }

Подключите `MetricsModule` к графу приложения. Остальные модули остаются такими же, как в HTTP-сервере.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends
            HoconConfigModule,
            JsonModule,
            LogbackModule,
            MetricsModule,  // <----- Подключили модуль
            UndertowHttpServerModule {

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application :
        HoconConfigModule,
        JsonModule,
        LogbackModule,
        MetricsModule,  // <----- Подключили модуль
        UndertowHttpServerModule
    ```

`MetricsModule` добавляет в граф `MeterRegistry`. Через него можно регистрировать собственные счетчики, таймеры, датчики и другие измерители.

## Конфигурация { #config }

Вынесите метрики на приватный порт. Публичный API остается на `8080`, а эксплуатационные пути живут на `8085`.

```hocon title="src/main/resources/application.conf"
httpServer {
  publicApiHttpPort = 8080
  privateApiHttpPort = 8085
  privateApiHttpMetricsPath = "/metrics"
}
```

Такой разнос важен для рабочего окружения: бизнес-клиенты не должны видеть внутренние метрики, а Prometheus, Kubernetes или другой агент мониторинга должны иметь простой стабильный путь для сбора данных.

## Сервис метрик { #metrics-service }

Создайте компонент `MetricsService`, но вводите его постепенно. Сначала сделаем простую метрику длительности, затем добавим счетчик, а потом усложним счетчик через тег email-провайдера.

### Таймер { #timer }

Начните с `MeterRegistry` и одного общего `Timer`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class MetricsService {

        private final MeterRegistry meterRegistry;
        private final Timer userCreationTimer;

        public MetricsService(MeterRegistry meterRegistry) {
            this.meterRegistry = meterRegistry;
            this.userCreationTimer = Timer.builder("user.creation.duration")
                    .description("Time taken to create users")
                    .register(meterRegistry);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class MetricsService(
        private val meterRegistry: MeterRegistry
    ) {
        private val userCreationTimer = Timer.builder("user.creation.duration")
            .description("Time taken to create users")
            .register(meterRegistry)
    }
    ```

`MeterRegistry` - это место, где регистрируются метрики. `Timer` измеряет длительность создания пользователя. Он общий для всех email-провайдеров, потому что время операции нас интересует как единый
сигнал: сколько в целом занимает создание пользователя.

#### Бакеты длительности { #duration-buckets }

Метрика длительности нужна не только для среднего значения. В рабочем окружении обычно важнее вопросы вроде "сколько операций быстрее 100 ms?", "не ухудшился ли 95-й перцентиль?" или "пора ли сработать оповещению, потому что слишком много запросов вышло за целевую задержку?". Для этого Micrometer может отдавать измерения по бакетам через целевые уровни обслуживания.

Обновите таймер и добавьте несколько практичных границ задержки:

===! ":fontawesome-brands-java: `Java`"

    ```java
    this.userCreationTimer = Timer.builder("user.creation.duration")
            .description("Time taken to create users")
            .serviceLevelObjectives(
                    Duration.ofMillis(50),
                    Duration.ofMillis(100),
                    Duration.ofMillis(250),
                    Duration.ofMillis(500))
            .register(meterRegistry);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    private val userCreationTimer = Timer.builder("user.creation.duration")
        .description("Time taken to create users")
        .serviceLevelObjectives(
            Duration.ofMillis(50),
            Duration.ofMillis(100),
            Duration.ofMillis(250),
            Duration.ofMillis(500),
        )
        .register(meterRegistry)
    ```

Эти значения не универсальны. Это пример бизнес-ориентиров: 50 ms - отлично, 100 ms - здоровое значение, 250 ms уже стоит наблюдать, а 500 ms для такой небольшой операции выглядит как явный сигнал тревоги. В реальном сервисе выбирайте границы под свою нагрузку и ожидания.

### Обертка операции { #operation-wrapper }

Теперь добавьте простую обертку без `email`. Она только измеряет длительность и возвращает результат операции:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public <T> T recordUserCreation(Callable<T> action) {
        try {
            return this.userCreationTimer.recordCallable(action);
        } catch (RuntimeException e) {
            throw e;
        } catch (Exception e) {
            throw new IllegalStateException("Failed to record user creation metrics", e);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun <T> recordUserCreation(action: Callable<T>): T {
        return try {
            userCreationTimer.recordCallable(action)
        } catch (e: RuntimeException) {
            throw e
        } catch (e: Exception) {
            throw IllegalStateException("Failed to record user creation metrics", e)
        }
    }
    ```

На этом шаге метрика отвечает только на вопрос "сколько длилась операция?". Если операция падает, исключение уходит наружу как раньше. Метрики не должны менять бизнес-поведение.

### Счетчик { #counter }

Теперь добавим вторую метрику: счетчик успешных созданий пользователя. Простой счетчик ответил бы только на вопрос "сколько пользователей создано?". Но часто хочется чуть больше контекста, например:
какие email-провайдеры чаще встречаются у новых пользователей.

Для этого используются теги. Тег - это короткая стабильная метка, которая добавляется к метрике и делит ее на группы. Например, одна и та же метрика `user.creation.total` может иметь разные значения тега `email.provider`: `gmail.com`, `example.com`, `company.org`.

Важно: тег должен быть стабильным и иметь ограниченное число вариантов. Хорошие значения тега обычно похожи на маршрут, провайдера, статус, результат или операцию. Плохие значения - полный email, идентификатор пользователя, идентификатор запроса, исходный путь запроса и другие данные, которые могут расти почти без ограничения.

Фреймворковые метрики Kora следуют тому же правилу. HTTP-метрики используют стабильные значения: метод, шаблон маршрута, хост, схему, код статуса и тип ошибки. Шаблон маршрута вроде `/users/{id}` безопасен, а исходный путь вроде `/users/128734` создавал бы новый ряд для каждого пользователя. Домен после `@` устроен так же: он не раскрывает конкретного пользователя и хорошо подходит для группировки.

#### Динамический тег { #dynamic-tag }

Теперь создайте счетчик с тегом `email.provider`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    private Counter userCreationCounter(String emailProvider) {
        return Counter.builder("user.creation.total")
                .description("Total number of users created")
                .tag("email.provider", emailProvider)
                .register(this.meterRegistry);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    private fun userCreationCounter(emailProvider: String): Counter {
        return Counter.builder("user.creation.total")
            .description("Total number of users created")
            .tag("email.provider", emailProvider)
            .register(meterRegistry)
    }
    ```

Теперь система мониторинга сможет показать не только общее число созданий, но и группы по провайдеру. После запросов с `alice@example.com` и `bob@gmail.com` вы увидите отдельные ряды для `example.com`
и `gmail.com`.

Для этого научите сервис получать провайдера из `email`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    private static String emailProvider(String email) {
        int at = email.indexOf('@');
        if (at < 0 || at == email.length() - 1) {
            return "unknown";
        }
        return email.substring(at + 1).toLowerCase(Locale.ROOT);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    private fun emailProvider(email: String): String {
        val provider = email.substringAfter('@', missingDelimiterValue = "")
        return provider.ifBlank { "unknown" }.lowercase()
    }
    ```

Если email некорректный или домен отсутствует, возвращаем `unknown`. Это лучше, чем создавать пустой тег или падать внутри метрики.

#### Кешировать метрики { #metric-caching }

Есть еще один прием для рабочего окружения, который стоит взять из внутренних метрик Kora: не пересобирать одну и ту же метрику с тегами на каждый запрос. Если у метрики нет динамических тегов, лучший вариант - создать ее один раз в конструкторе и хранить как `final` поле, как мы сделали с `userCreationTimer`. Тогда на горячем пути запроса код только вызывает `record(...)` или `increment()`, а вся сборка измерителя уже завершена при создании компонента.

С динамическими тегами ситуация другая. Значение `email.provider` известно только во время обработки конкретного пользователя, поэтому нельзя заранее создать один общий `final Counter`: для `gmail.com`, `example.com` и `company.org` нужны разные временные ряды одной метрики. Но это не значит, что счетчик надо собирать заново на каждый запрос. Правильная форма - создать счетчик один раз для каждого нового провайдера и дальше переиспользовать его.

Внутри Micrometer измеритель определяется не только именем, но и полным набором тегов. Когда вызывается `Counter.builder(...).tag(...).register(meterRegistry)`, Micrometer собирает идентификатор измерителя, проверяет реестр и возвращает уже существующий измеритель или регистрирует новый. Даже если реестр умеет не плодить дубликаты, постоянный вызов построителя на каждом запросе все равно заставляет код снова создавать построитель, описание, теги и проходить регистрацию. Это лишняя работа на самом частом пути приложения.

Сделайте то же самое для `email.provider`. Добавьте небольшой кеш счетчиков:

===! ":fontawesome-brands-java: `Java`"

    ```java
    private final ConcurrentHashMap<String, Counter> userCreationCounters = new ConcurrentHashMap<>();

    private Counter userCreationCounter(String emailProvider) {
        return this.userCreationCounters.computeIfAbsent(emailProvider, provider ->
                Counter.builder("user.creation.total")
                        .description("Total number of users created")
                        .tag("email.provider", provider)
                        .register(this.meterRegistry));
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    private val userCreationCounters = ConcurrentHashMap<String, Counter>()

    private fun userCreationCounter(emailProvider: String): Counter {
        return userCreationCounters.computeIfAbsent(emailProvider) { provider ->
            Counter.builder("user.creation.total")
                .description("Total number of users created")
                .tag("email.provider", provider)
                .register(meterRegistry)
        }
    }
    ```

Метрика все еще создается лениво: счетчик для `gmail.com` появится только тогда, когда пройдет успешная операция с Gmail-адресом. После этого тот же счетчик будет переиспользоваться. На следующих запросах с `gmail.com` `computeIfAbsent` просто вернет уже зарегистрированный `Counter`, и код сразу вызовет `increment()`.

Такой кеш не нужен для каждого измерителя. Если набор тегов фиксированный, держите измеритель как поле сервиса. Кеш нужен именно там, где тег появляется из данных времени выполнения, но эти данные остаются низкокардинальными и пригодными для группировки. В итоге код явно показывает границу тега, не делает лишнюю работу построителя и регистрации на каждом вызове и остается похожим на подход Kora к системным HTTP-метрикам.

### Финальная обертка операции { #final-wrapper }

Последний шаг - обновить обертку операции. Теперь она принимает `email`, измеряет длительность через таймер, а после успешного выполнения увеличивает счетчик с тегом провайдера.

===! ":fontawesome-brands-java: `Java`"

    ```java
    public <T> T recordUserCreation(String email, Callable<T> action) {
        try {
            var result = this.userCreationTimer.recordCallable(action);
            this.userCreationCounter(emailProvider(email)).increment();
            return result;
        } catch (RuntimeException e) {
            throw e;
        } catch (Exception e) {
            throw new IllegalStateException("Failed to record user creation metrics", e);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun <T> recordUserCreation(email: String, action: Callable<T>): T {
        return try {
            val result = userCreationTimer.recordCallable(action)
            userCreationCounter(emailProvider(email)).increment()
            result
        } catch (e: RuntimeException) {
            throw e
        } catch (e: Exception) {
            throw IllegalStateException("Failed to record user creation metrics", e)
        }
    }
    ```

Порядок важен: счетчик увеличивается только после успешной операции. Так `user.creation.total` считает созданных пользователей, а не любые попытки вызвать метод.

### Итоговый сервис { #complete-service }

В итоговом виде компонент остается небольшим, но теперь каждая часть уже понятна:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class MetricsService {

        private final MeterRegistry meterRegistry;
        private final Timer userCreationTimer;
        private final ConcurrentHashMap<String, Counter> userCreationCounters = new ConcurrentHashMap<>();

        public MetricsService(MeterRegistry meterRegistry) {
            this.meterRegistry = meterRegistry;
            this.userCreationTimer = Timer.builder("user.creation.duration")
                    .description("Time taken to create users")
                    .serviceLevelObjectives(
                            Duration.ofMillis(50),
                            Duration.ofMillis(100),
                            Duration.ofMillis(250),
                            Duration.ofMillis(500))
                    .register(meterRegistry);
        }

        public <T> T recordUserCreation(String email, Callable<T> action) {
            try {
                var result = this.userCreationTimer.recordCallable(action);
                this.userCreationCounter(emailProvider(email)).increment();
                return result;
            } catch (RuntimeException e) {
                throw e;
            } catch (Exception e) {
                throw new IllegalStateException("Failed to record user creation metrics", e);
            }
        }

        private Counter userCreationCounter(String emailProvider) {
            return this.userCreationCounters.computeIfAbsent(emailProvider, provider ->
                    Counter.builder("user.creation.total")
                            .description("Total number of users created")
                            .tag("email.provider", provider)
                            .register(this.meterRegistry));
        }

        private static String emailProvider(String email) {
            int at = email.indexOf('@');
            if (at < 0 || at == email.length() - 1) {
                return "unknown";
            }
            return email.substring(at + 1).toLowerCase(Locale.ROOT);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class MetricsService(
        private val meterRegistry: MeterRegistry
    ) {
        private val userCreationTimer = Timer.builder("user.creation.duration")
            .description("Time taken to create users")
            .serviceLevelObjectives(
                Duration.ofMillis(50),
                Duration.ofMillis(100),
                Duration.ofMillis(250),
                Duration.ofMillis(500),
            )
            .register(meterRegistry)
        private val userCreationCounters = ConcurrentHashMap<String, Counter>()

        fun <T> recordUserCreation(email: String, action: Callable<T>): T {
            return try {
                val result = userCreationTimer.recordCallable(action)
                userCreationCounter(emailProvider(email)).increment()
                result
            } catch (e: RuntimeException) {
                throw e
            } catch (e: Exception) {
                throw IllegalStateException("Failed to record user creation metrics", e)
            }
        }

        private fun userCreationCounter(emailProvider: String): Counter {
            return userCreationCounters.computeIfAbsent(emailProvider) { provider ->
                Counter.builder("user.creation.total")
                    .description("Total number of users created")
                    .tag("email.provider", provider)
                    .register(meterRegistry)
            }
        }

        private fun emailProvider(email: String): String {
            val provider = email.substringAfter('@', missingDelimiterValue = "")
            return provider.ifBlank { "unknown" }.lowercase()
        }
    }
    ```

## Интеграция сервиса { #service-integration }

Внедрите `MetricsService` в `UserService` и оберните создание пользователя. Email передается в метрики отдельно, потому что именно из него `MetricsService` извлекает тег провайдера.

===! ":fontawesome-brands-java: `Java`"

    ```java
    public UserResponse createUser(UserRequest request) {
        return metricsService.recordUserCreation(request.email(), () -> {
            var generatedId = userRepository.save(request.name(), request.email());
            return new UserResponse(generatedId, request.name(), request.email(), LocalDateTime.now());
        });
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun createUser(request: UserRequest): UserResponse {
        return metricsService.recordUserCreation(request.email) {
            val id = userRepository.save(request.name, request.email)
            UserResponse(id, request.name, request.email, LocalDateTime.now())
        }
    }
    ```

Размещайте бизнес-метрики на уровне сервиса, а не контроллера. Контроллер знает HTTP-форму запроса, но сервис лучше знает, произошла ли предметная операция.

## Проверка приложения { #check-app }

Запустите приложение, создайте двух пользователей с разными email-доменами и откройте метрики:

```bash
curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice","email":"alice@example.com"}'

curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -d '{"name":"Bob","email":"bob@gmail.com"}'

curl http://localhost:8085/metrics
```

В выводе должны появиться строки с `user.creation.duration` и `user.creation.total`. Для счетчика также должен быть виден тег провайдера со значениями вроде `example.com` и `gmail.com`. Конкретная система мониторинга может нормализовать имя тега, например превратить `email.provider` в `email_provider`.

Если метрик нет, проверьте три вещи: подключен ли `MetricsModule`, попадает ли код в `recordUserCreation()`, и смотрит ли `curl` на приватный порт.

## Лучшие практики { #best-practices }

- Начинайте с небольшого числа бизнес-метрик, которые отвечают на реальные эксплуатационные вопросы.
- Не добавляйте теги с пользовательскими идентификаторами, полным email, исходным путем запроса или другими значениями высокой кардинальности.
- Нормализуйте теги: `gmail.com` лучше, чем полный `bob@gmail.com`.
- Держите имена метрик стабильными: панели мониторинга и оповещения зависят от них как от API.
- Измеряйте длительность вокруг фактической операции, а не вокруг подготовки DTO.
- Оставляйте `/metrics` на приватном порту.

## Итоги { #summary }

Вы добавили в приложение Micrometer, вынесли `/metrics` на приватный порт, измерили длительность создания пользователя и посчитали успешные создания с тегом email-провайдера.

## Ключевые понятия { #key-concepts }

Counter:
: считает количество событий и может разделять их по стабильным тегам.

Timer:
: измеряет длительность и распределение времени выполнения.

Tag:
: стабильная метка для группировки рядов метрик.

MeterRegistry:
: точка регистрации пользовательских метрик в графе Kora.

Закрытый управляющий порт:
: отдельный порт для эксплуатационных путей.

## Устранение неполадок { #troubleshooting }

Метрика не появилась:
: Убедитесь, что операция реально была вызвана после старта приложения.

`/metrics` не открывается:
: Проверьте `privateApiHttpPort` и `privateApiHttpMetricsPath`.

Слишком много рядов в мониторинге:
: Уберите теги с динамическими значениями.

## Что дальше? { #whats-next }

- добавьте трассировку в [руководстве по трассировке](observability-tracing.md)
- добавьте проверки готовности и живости в [руководстве по пробам](observability-probes.md)
- сравните детали с [документацией по метрикам](../documentation/metrics.md)

## Помощь { #help }

- проверьте готовые Java и Kotlin приложения observability
- сверяйте имена модулей с [документацией по метрикам](../documentation/metrics.md)
