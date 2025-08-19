---
search:
  exclude: true
---

Первое знакомство с Kora рекомендуется начать с [ознакомительного примера](hello-world.md) с пояснениями, 
где показаны основы настройки проекта и создания примитивного примера сервиса.

Большое количество рабочих и актуальных примеров сервисов с использованием различных Kora модулей можно найти в данном 
[репозитории](https://github.com/kora-projects/kora-examples).

Там собраны примеры работы с 
[CRUD-сервис](https://github.com/kora-projects/kora-examples/tree/master/kora-java-crud),
[HTTP сервером](https://github.com/kora-projects/kora-examples/tree/master/kora-java-http-server), 
[HTTP клиентом](https://github.com/kora-projects/kora-examples/tree/master/kora-java-http-client),
[базой данных](https://github.com/kora-projects/kora-examples/tree/master/kora-java-database-jdbc), 
[Kafka](https://github.com/kora-projects/kora-examples/tree/master/kora-java-kafka), 
[OpenAPI кодогенерацией](https://github.com/kora-projects/kora-examples/tree/master/kora-java-openapi-generator-http-client) 
и другими различными модулями Kora.

К каждому сервису примеру прилагаются тесты посредствам которых можно проверить работоспособность сервиса и
посмотреть как писать примитивные тесты к определенному функционалу, как с использованием 
[JUnit 5 расширения](https://github.com/kora-projects/kora-examples/blob/master/kora-java-crud/src/test/java/ru/tinkoff/kora/example/crud/ComponentTests.java), 
так и в формате черного ящика с использованием 
[TestContainers](https://github.com/kora-projects/kora-examples/blob/master/kora-java-crud/src/test/java/ru/tinkoff/kora/example/crud/BlackBoxTests.java).

=== ":fontawesome-brands-java: `Java`"

    Создать новый Java сервис можно использовав [шаблон на GitHub](https://github.com/kora-projects/kora-java-template)

=== ":simple-kotlin: `Kotlin`"

    Создать новый Kotlin сервис можно использовав [шаблон на GitHub](https://github.com/kora-projects/kora-kotlin-template)
