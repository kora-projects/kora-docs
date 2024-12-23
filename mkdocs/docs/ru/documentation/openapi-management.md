Модуль для предоставления OpenAPI файла из приложения, 
а также [Swagger UI](https://swagger.io/tools/swagger-ui/) и [Rapidoc](https://rapidocweb.com/) для отображения OpenAPI.

## Подключение

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#_4) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:openapi-management"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends OpenApiManagementModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#_4) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:openapi-management")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : OpenApiManagementModule
    ```

Требует подключения [HTTP сервера](http-server.md).

## Конфигурация

Пример конфигурации описанной в классе `OpenApiManagementConfig`:

===! ":material-code-json: `Hocon`"

    ```javascript
    openapi {
        management {
            file = [ "my-openapi-1.yaml", "my-openapi-2.yaml" ] //(1)!
            enabled = false  //(2)!
            endpoint = "/openapi" //(3)!
            swaggerui {
                enabled = false //(4)!
                endpoint = "/swagger-ui" //(5)!
            }
            rapidoc {
                enabled = false //(6)!
                endpoint = "/rapidoc" //(7)!
            }
        }
    }
    ```

    1.  Относительный путь до OpenAPI файлов в `resources` директории, можно указывать как один файл, так и несколько файлов
    2.  Вкл/Выкл контроллера который отдает OpenAPI 
    3.  Путь по которому будет доступен OpenAPI
        1. Если указан один OpenAPI файл, является целиком путем по которому доступен файл
        2. Если указаны несколько OpenAPI файлов, является префиксом к пути перед именем файла `/openapi/{fileName}`, берется указанный путь и к нему добавляется имя файла без диреторий и его расширения, в случае файла `someDirectory/my-openapi-1.yaml` путь к файлу будет `/openapi/my-openapi-1`
    4.  Вкл/Выкл контроллера который отдает SwaggerUI
    5.  Путь по которому будет доступен SwaggerUI
    6.  Вкл/Выкл контроллера который отдает Rapidoc
    7.  Путь по которому будет доступен Rapidoc

=== ":simple-yaml: `YAML`"

    ```yaml
    openapi:
      management:
        file: [ "my-openapi-1.yaml", "my-openapi-2.yaml" ] #(1)!
        enabled: false  #(2)!
        endpoint: "/openapi" #(3)!
        swaggerui:
          enabled: false #(4)!
          endpoint: "/swagger-ui" #(5)!
        rapidoc:
          enabled: false #(6)!
          endpoint: "/rapidoc" #(7)!
    ```

    1.  Относительный путь до OpenAPI файлов в `resources` директории, можно указывать как один файл, так и несколько файлов
    2.  Вкл/Выкл контроллера который отдает OpenAPI 
    3.  Путь по которому будет доступен OpenAPI
        1. Если указан один OpenAPI файл, является целиком путем по которому доступен файл
        2. Если указаны несколько OpenAPI файлов, является префиксом к пути перед именем файла `/openapi/{fileName}`, берется указанный путь и к нему добавляется имя файла без диреторий и его расширения, в случае файла `someDirectory/my-openapi-1.yaml` путь к файлу будет `/openapi/my-openapi-1`
    4.  Вкл/Выкл контроллера который отдает SwaggerUI
    5.  Путь по которому будет доступен SwaggerUI
    6.  Вкл/Выкл контроллера который отдает Rapidoc
    7.  Путь по которому будет доступен Rapidoc

## Рекомендации

???+ warning "Совет"

    Мы рекомендуем использовать подход когда первичен [контракт и по нему создается код](openapi-codegen.md), 
    в таком подходе отображается этот самый файл контракт.

    В случае же когда первичен код и по нему предполагается создавать файл контракт, можно использовать [Swagger Gradle Plugin](https://github.com/swagger-api/swagger-core/blob/master/modules/swagger-gradle-plugin/README.md)
    вкупе с [набором Swagger аннотаций](https://github.com/swagger-api/swagger-core/wiki/Swagger-2.X---Annotations) по которым будет создаваться файл контракт.
