---
title: OpenAPI-First Development with the Kora Framework
date: 2026-08-25
description: Why contract-first OpenAPI development in the Kora Framework generates typed servers, clients, and errors from one source of truth.
search:
  exclude: true
---

# OpenAPI-First Development with Kora { #openapi-first }

**August 25, 2026**

OpenAPI is often introduced as documentation. A team writes controllers, request DTOs, response DTOs, validation annotations, security annotations, and exception mappings, and only after the
application already exists does a plugin inspect that code and emit an `openapi.json` file. Swagger UI renders it, client generators may consume it, and the file is called an API contract.

Technically, it describes the API. Architecturally, however, it is not really the contract. The implementation is the contract and the OpenAPI document is only a report about what the framework
believes the implementation currently does.

Kora supports a stronger model:

```text
openapi.yaml
    ↓
Kora Generator
    ↓
typed models
typed server API
typed client
typed errors
```

In this model the OpenAPI specification is not an artifact reconstructed after implementation. It is the authoritative transport contract from which both sides of an HTTP boundary can be generated.
The server is written against it. The client is generated from it. Request and response models derive from it. Status codes, validation constraints, security schemes, media types, multipart fields,
and declared failures are part of the same source of truth.

That difference is much larger than choosing YAML instead of annotations. It changes where API design happens, when compatibility problems are discovered, how producer and consumer teams coordinate,
and how much transport plumbing must be maintained manually.

Kora's architecture fits this model particularly well because the rest of the framework follows the same pattern: describe intent, analyze structure at build time, generate readable typed source,
validate it with the compiler, and keep runtime machinery small. OpenAPI-first development simply extends that philosophy across a network boundary.

---

## The Important Question Is Direction of Authority { #direction-of-authority }

The same OpenAPI document can exist in two very different architectures.

In a code-first system:

```text
implementation
    ↓
framework annotations and runtime conventions
    ↓
OpenAPI document
```

The implementation owns the API. The specification is descriptive.

In a contract-first system:

```text
OpenAPI document
    ↓
generated server and client contracts
    ↓
implementation
```

The specification owns the API. The implementation is constrained by it.

That is the central distinction.

A contract should sit above implementations. If two services communicate through HTTP, neither side should have to reconstruct the protocol independently. Both should consume a shared description of
that protocol, just as two classes inside one process can compile against the same Java interface.

Consider a service boundary:

```text
Orders Service
      ↓ HTTP
Payments Service
```

A weak model is:

```text
Orders controller implementation
      ↓
documentation
      ↓
Payments team manually writes matching client
```

A stronger model is:

```text
        OpenAPI contract
        /              \
       ↓                ↓
generated server    generated client
       ↓                ↓
Orders logic       Payments logic
```

The protocol becomes an independent architectural artifact rather than an accidental consequence of one framework's controller model.

---

## Why OpenAPI Should Be a Contract, Not Generated JSON { #contract-not-json }

Generating OpenAPI from annotations is useful. It can produce documentation, Swagger UI, API catalogs, and client generation inputs. For many small applications that may be entirely sufficient.

The limitation appears when the API is a long-lived boundary between independently changing systems.

Suppose a developer renames a DTO field because it reads better in Java. If OpenAPI is generated from implementation, that refactoring may silently become an external protocol change. Suppose an
exception mapper changes a status code. The contract changes because the implementation changed. Suppose a controller parameter annotation changes requiredness. Consumers may see a different API even
though nobody explicitly reviewed an API change.

Contract-first reverses that relationship.

The external API changes only when the contract changes. Internal implementation can be refactored freely as long as it continues to satisfy the same generated server interface.

This restores a fundamental software-engineering property that is surprisingly easy to lose in microservices: encapsulation.

Internal classes should be replaceable without changing external behavior.

---

## One Contract, Two Typed Boundaries { #two-typed-boundaries }

Kora's OpenAPI generator can create both declarative HTTP server infrastructure and declarative HTTP clients from an OpenAPI description. It also generates models and the mapping infrastructure
required to move data through that boundary.

Conceptually:

```text
                    openapi.yaml
                    /          \
                   /            \
                  ↓              ↓
          generated server   generated client
                  ↓              ↓
          producer logic     consumer logic
```

The important property is not merely that code generation saves typing. It is that both sides derive their interpretation of the protocol from the same source.

Without generation, protocol facts are duplicated manually:

```text
HTTP method
path
path parameter names
query parameter names
headers
JSON properties
required fields
enum values
content types
status codes
error payloads
security requirements
```

Every duplicated fact is an opportunity for drift.

Generation changes the model from duplication to derivation.

---

## The Server Implements the Contract Instead of Re-Declaring It { #server-implements-contract }

In a contract-first Kora server, application code should not have to restate HTTP mechanics that are already present in the specification.

If `openapi.yaml` says:

```text
GET /users/{id}
```

with an `int64` path parameter and the responses:

```text
200 → User
404 → NotFoundProblem
```

then those are already protocol facts.

The generated server layer can translate them into a typed Java or Kotlin API. Application code can focus on implementing the behavior behind the operation rather than repeating route, parameter,
serialization, validation, and response metadata.

A simplified conceptual shape might be:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public interface UsersApiDelegate {
        GetUserResponse getUser(long id);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    interface UsersApiDelegate {
        fun getUser(id: Long): GetUserResponse
    }
    ```

The exact generated code depends on generator options and the specification, but the architectural separation is what matters:

```text
OpenAPI:
defines protocol

Generated Kora layer:
implements transport mechanics

Handwritten delegate/service:
implements business behavior
```

That keeps controllers from becoming a second hand-maintained API specification.

---

## Business Code Should Not Describe HTTP Twice { #no-http-twice }

Code-first APIs often contain several overlapping descriptions of the same endpoint. The controller defines the path and method. DTO annotations influence the schema. validation annotations describe
field constraints. security annotations describe authentication. Swagger annotations add examples and response metadata. Exception handlers determine errors.

Then all of that is transformed into OpenAPI.

The architecture effectively maintains two languages for one boundary:

```text
framework-specific Java/Kotlin metadata
        ↓
standard OpenAPI metadata
```

If OpenAPI is already the artifact that clients, gateways, QA, documentation systems, security scanners, and external teams understand, making it the original source removes an unnecessary
synchronization problem.

The transport contract should be written once.

The Java/Kotlin representation should be generated.

---

## Generated Models Eliminate DTO Drift { #dto-drift }

One of the most common integration problems is a mismatch between producer and consumer models.

The server believes a response is:

```json
{
    "userId": 123,
    "name": "Alice"
}
```

while a manually maintained client assumes:

```json
{
    "id": "123",
    "displayName": "Alice"
}
```

Typed clients help, but they are only as trustworthy as their relationship to the server contract.

With OpenAPI-first generation, both producer and consumer models derive from the same schema:

```text
              schema
              /    \
             ↓      ↓
      server model client model
```

They do not need to share the same physical JAR or Java class. In fact, sharing server DTO JARs across service boundaries can create undesirable implementation coupling. What matters is that the wire
representations are projections of the same language-neutral contract.

This preserves service autonomy while reducing protocol drift.

---

## Transport Models Are Not Necessarily Domain Models { #transport-vs-domain }

Generated OpenAPI models describe the wire. They should not automatically become the entire business domain.

A mature service may have:

```text
CreateOrderRequest
OrderResponse
MoneyDto
```

at the API boundary, while its domain uses:

```text
Order
Money
CustomerId
OrderState
```

with stronger invariants.

A healthy architecture can therefore look like:

```text
HTTP
 ↓
generated OpenAPI request
 ↓
mapping
 ↓
domain command
 ↓
business logic
 ↓
domain result
 ↓
mapping
 ↓
generated OpenAPI response
```

For a small CRUD service this separation may be unnecessary. Generated models can sometimes be used directly. But for long-lived APIs, explicit transport/domain separation prevents external protocol
choices from controlling internal architecture.

Kora's compile-time approach to mapping makes such boundaries relatively cheap to maintain.

---

## Generated Source Should Be Replaceable { #generated-source-replaceable }

The OpenAPI file is authoritative only if generated code remains disposable.

The rule should be:

> Changing the contract and regenerating must never destroy hand-written business logic.

Generated output should contain the transport machinery:

```text
models
server interfaces/delegates
controller adapters
client interfaces
response mappings
security glue
```

Handwritten source should contain application behavior:

```text
services
domain logic
repositories
policies
delegate implementations
```

If developers manually patch generated classes, the source of truth becomes ambiguous. The YAML says one thing, generated source says another, and regeneration becomes dangerous.

Generated source should be inspectable, but not hand-owned.

---

## Compile-Time Types Turn Contract Changes into Build Failures { #compile-time-types }

The most important benefit of Kora's approach is not reduced boilerplate. It is that contract changes become compiler-visible.

Suppose a response schema changes from:

```text
User
```

to:

```text
UserDetails
```

After regeneration, the server delegate and generated client signatures change. Handwritten code that still expects the old type can fail compilation.

That failure is useful.

It means:

```text
your implementation no longer satisfies the declared external contract
```

The same principle applies to parameter types, request models, response variants, or required fields.

HTTP normally weakens static guarantees because producer and consumer are separated by a network. Generation recovers part of that lost type safety.

---

## A Breaking Contract Change Should Be Painful Early { #breaking-change-early }

Imagine changing:

```text
GET /users/{id}
```

from an integer identifier to a UUID string.

In a raw HTTP system, several codebases may continue compiling and only fail when traffic reaches the changed endpoint.

With generated server and client code, regeneration changes method types. Call sites and delegate implementations can fail immediately.

That is exactly the correct behavior.

The transport equivalent of changing a Java interface should behave like changing a Java interface: incompatible implementations should stop compiling.

Contract-first development makes breaking API changes visible where they are cheapest to fix.

---

## Generated Clients Are About Authority, Not Convenience { #generated-clients-authority }

A generated HTTP client is often presented as a productivity tool because developers do not have to write URLs, serialize JSON, or switch on status codes.

That is useful, but the deeper advantage is architectural.

A handwritten client is a second independent interpretation of the remote API.

For example:

```http
POST /users
Content-Type: application/json
```

plus:

===! ":fontawesome-brands-java: `Java`"

    ```java
    if (status == 200) ...
    else if (status == 404) ...
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    if (status == 200) ...
    else if (status == 404) ...
    ```

duplicates protocol knowledge already owned by the producer.

A generated client says something stronger:

```text
this source code was derived from the same contract
that defines the server boundary
```

The difference is not fewer lines.

It is fewer independently maintained truths.

---

## Typed Errors Are Part of a Real Contract { #typed-errors }

Many API stacks remain strongly typed only on the happy path.

A generated method may expose:

===! ":fontawesome-brands-java: `Java`"

    ```java
    User getUser(...)
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun getUser(...): User
    ```

but every non-2xx response becomes a generic exception containing:

```text
status code
raw body
headers
```

The caller then writes integer-based error handling:

===! ":fontawesome-brands-java: `Java`"

    ```java
    catch (HttpException e) {
        if (e.statusCode() == 404) {
            ...
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    catch (e: HttpException) {
        if (e.statusCode == 404) {
            ...
        }
    }
    ```

At that point the API stopped being typed exactly where consumers most need semantic information.

Expected error responses are part of the protocol.

An API may deliberately declare:

```text
200 User
404 NotFoundProblem
409 ConflictProblem
422 ValidationProblem
```

These are not equivalent to:

```text
DNS failure
connection reset
TLS failure
malformed response
```

A strong generated client should preserve that distinction:

```text
HTTP result
├── declared success
│   └── typed success model
├── declared error/business response
│   └── typed error model
└── undeclared or transport failure
    └── infrastructure exception
```

Kora's recent OpenAPI work has continued to strengthen generated response contracts and typed client/error behavior because this is fundamental to making generated clients useful beyond trivial
success cases.

---

## Status Codes Are Part of the Type System { #status-codes-type-system }

HTTP already contains a response discriminator: the status code.

The contract should use it deliberately.

Consider:

```text
POST /orders

201 → Order
400 → ValidationProblem
409 → ExistingOrder
```

A consumer should be able to reason in protocol outcomes rather than raw integers and manually decoded bodies.

Conceptually:

===! ":fontawesome-brands-java: `Java`"

    ```java
    switch (result) {
        case Created created -> ...
        case BadRequest invalid -> ...
        case Conflict existing -> ...
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    when (result) {
        is Created -> ...
        is BadRequest -> ...
        is Conflict -> ...
    }
    ```

This makes the declared HTTP behavior part of the source-level API.

A generic `2xx body / everything else exception` model loses valuable information that was already present in OpenAPI.

---

## Declared Errors Improve Resilience Decisions { #declared-errors-resilience }

Typed failure semantics are also important for retries and circuit breakers.

A `409 Conflict` may be a terminal business result.

A `429 Too Many Requests` may be retryable after a delay.

A network timeout may be retryable only if the operation is idempotent.

A `401 Unauthorized` usually requires authentication correction rather than another identical request.

If every failure becomes the same exception, resilience logic has to reconstruct meaning from status codes and strings.

A contract that models errors explicitly gives the client enough information to make safer decisions.

OpenAPI therefore influences reliability architecture, not just documentation.

---

## Expected Failure and Unexpected Failure Must Stay Different { #expected-vs-unexpected }

A client still needs a generic failure path.

If the contract declares:

```text
200
404
409
```

but the server returns:

```text
502
```

that is not a declared business response.

Likewise, malformed JSON or a transport timeout cannot be represented by a declared model.

A good generated boundary preserves two categories:

```text
contract outcomes
```

and:

```text
protocol/transport violations
```

Collapsing them would make the contract less trustworthy.

Unexpected responses should remain visible because they may indicate deployment skew, proxy behavior, server bugs, or stale specifications.

---

## Security Belongs in the Contract { #security-in-contract }

Security is another area where implementation-first systems often maintain several independent sources of truth.

The controller says authentication is required. The API gateway separately says authentication is required. Documentation says authentication is required. The generated client has separate
configuration.

OpenAPI can declare security schemes and operation-level security requirements directly.

For example:

```yaml
components:
    securitySchemes:
        bearerAuth:
            type: http
            scheme: bearer
```

and:

```yaml
security:
    -   bearerAuth: [ ]
```

The Kora Framework can use these declarations when generating server and client integration points.

This makes authentication requirements visible before implementation exists and creates a clear review surface for questions such as:

- Is this operation public?
- Which authentication mechanism applies?
- Are multiple mechanisms supported?
- Is anonymous fallback intentional?

The contract does not replace business authorization logic, but it should describe the transport-level security agreement.

---

## Contract Security Is Not Domain Authorization { #security-vs-authorization }

An OpenAPI document can say:

```text
bearer token required
```

It cannot meaningfully express every rule such as:

```text
the current user may cancel only orders they own
```

That belongs in domain/application logic.

A clean separation is:

```text
authentication transport
→ OpenAPI + generated Kora integration

authorization policy
→ application/domain
```

This prevents the specification from becoming a substitute for business architecture.

---

## Validation Should Be Split the Same Way { #validation-split }

OpenAPI can express transport validation:

```text
required
minLength
maxLength
pattern
minimum
maximum
enum
format
```

Kora can generate server-side validation integration from these declarations.

That avoids defining the same boundary rule once in YAML and again manually in Java.

But complex business rules still belong in the domain.

For example:

```text
amount must be positive
```

may be a transport/schema rule.

While:

```text
amount must not exceed remaining credit limit
```

requires business state and belongs deeper in the application.

The pipeline becomes:

```text
OpenAPI validation
→ structurally valid request
→ business validation
→ semantically valid operation
```

---

## Required, Optional, and Nullable Are Different Contracts { #required-optional-nullable }

One of the easiest ways to produce bad generated APIs is to treat all absent/null states as equivalent.

These are different:

```text
required and non-null
optional but non-null when present
required but nullable
optional and nullable
```

They can have very different meanings in Java, Kotlin, serialization, PATCH semantics, and backwards compatibility.

For an update request:

```json
{}
```

may mean:

```text
leave displayName unchanged
```

while:

```json
{
    "displayName": null
}
```

may mean:

```text
clear displayName
```

A simple nullable field cannot necessarily represent both states.

OpenAPI-first development makes these semantics a deliberate API-design issue rather than a serializer accident.

Kora's generator exposes configuration around nullable and optional representations because the wire distinction is real.

---

## Error Schemas Need Real Design { #error-schemas }

Teams often carefully design successful models while treating errors as an afterthought:

```text
500 → Error
```

That produces poor clients.

For every operation, ask:

- Which failures are expected?
- Which are normal business outcomes?
- Which are retryable?
- Which schema is returned?
- Does the consumer need a stable machine-readable error code?
- Can it distinguish invalid input from conflict?
- Is correlation information useful?

A shared problem schema can be valuable:

```json
{
    "code": "ORDER_ALREADY_EXISTS",
    "message": "Order already exists",
    "traceId": "..."
}
```

But avoid making every error one generic bag of strings when more precise schemas would materially help consumers.

Typed client errors are only as good as the contract that defines them.

---

## Machine-Readable Errors Beat Message Parsing { #machine-readable-errors }

Consumers should never need logic such as:

```text
if message contains "already exists"
```

Human-readable messages may change.

Machine-readable error semantics should not.

If consumers need to branch on an error, represent that fact structurally through status, schema, stable code, or a combination of them.

Contract-first design forces these decisions into the open.

That is exactly where they belong.

---

## OpenAPI-First Enables Real Compatibility Checking { #compatibility-checking }

Once the OpenAPI file is the primary contract, CI can compare:

```text
previous contract
vs
new contract
```

and detect potentially breaking changes before implementation ships.

Examples include:

- removed operations;
- removed response types;
- incompatible schema changes;
- new required request fields;
- narrowed enums;
- changed parameter locations;
- changed security requirements.

Not every syntactic change has obvious semantic compatibility, so tools cannot replace judgment entirely. But they can catch a large class of accidental breakage.

This is much stronger than reviewing generated Swagger output after a controller change has already been merged.

---

## Compatibility Should Be a Build Gate { #compatibility-build-gate }

A strong API pipeline looks like:

```text
edit openapi.yaml
    ↓
validate specification
    ↓
lint organizational rules
    ↓
compare compatibility
    ↓
generate Kora code
    ↓
compile
    ↓
test
```

The contract is effectively compiled twice.

First, API tooling checks whether the document is internally valid and compatible with policy.

Then Kora/OpenAPI generation turns it into Java/Kotlin types, and the normal compiler checks application code against those types.

This is a very powerful feedback loop.

---

## API Review Happens Before Implementation Becomes Expensive { #api-review-early }

Suppose a proposed endpoint:

```text
POST /payments
```

has several problems:

- wrong success status;
- no idempotency key;
- vague error representation;
- unnecessary nullable fields;
- internal database identifiers exposed;
- inconsistent naming;
- missing authentication.

If the API is discovered only after controller implementation, DTO creation, tests, and downstream integration have begun, redesign is expensive.

With contract-first development:

```text
design
→ review
→ generate
→ implement
```

Those issues can be fixed while they are still text changes in a specification.

The cheapest time to repair an API is before consumers exist.

---

## Contract Diffs Are Better API Review Surfaces { #contract-diffs }

A contract pull request can show something as direct as:

```diff
 responses:
   '201':
     ...
+  '409':
+    description: Order already exists
+    content:
+      application/json:
+        schema:
+          $ref: '#/components/schemas/ExistingOrder'
```

The reviewer immediately sees that external behavior changed.

With implementation-first development, the same semantic change may be scattered across an exception class, controller advice, DTO, annotations, and tests.

The OpenAPI diff is not merely documentation.

It is an architectural diff.

---

## Contract-First Enables Parallel Team Development { #parallel-team-development }

This is one of the largest organizational benefits.

Suppose Team A builds an Orders service and Team B consumes it.

Code-first sequencing often looks like:

```text
Team A implements
    ↓
Team A produces usable API description
    ↓
Team B writes client
```

The dependency is sequential.

Contract-first changes it:

```text
Teams agree on OpenAPI
        ↓
        ├── Team A generates server and implements
        └── Team B generates client and integrates
```

Both teams can work in parallel.

Mocks can be built from the specification.

Consumer code can compile before the real server exists.

The calendar-time saving can be much larger than the code-generation saving.

---

## OpenAPI Is a Better Cross-Language Boundary Than Annotations { #cross-language-boundary }

Kora may implement the server in Java or Kotlin, but consumers may be:

```text
Go
TypeScript
Python
Swift
Kotlin Android
another Java service
```

A framework-specific controller annotation model has little value to those consumers.

OpenAPI is intentionally language-neutral.

This gives a useful boundary:

> Kora can be opinionated about implementation while the external contract remains ecosystem-neutral.

That is an excellent property for service architecture.

---

## Do Not Share Server DTO JARs as the Contract { #no-dto-jars }

Java organizations sometimes avoid client generation by publishing a shared DTO dependency.

For example:

```text
orders-api-models.jar
```

Consumers import it directly.

This appears typed but creates coupling to:

- Java;
- server package structure;
- server release process;
- serialization choices;
- implementation classes.

A versioned OpenAPI contract is a cleaner interface.

JVM consumers can still generate strongly typed classes from it, but those classes are transport projections rather than shared producer implementation.

The distinction matters for service independence.

---

## Contract Artifacts Can Be Versioned Independently { #versioned-contract-artifacts }

In a mature platform, the OpenAPI contract can be published as a versioned artifact:

```text
orders-api:2.4.0
```

The server implementation compiles against that contract.

Consumers pin a compatible version and generate clients.

This separates:

```text
API contract version
```

from:

```text
server build version
```

A service may deploy dozens of internal builds without changing its external API.

Consumers should not need to follow every implementation release.

Versioning the contract directly makes that explicit.

---

## Multiple Contracts Can Be Healthier Than One Giant Specification { #multiple-contracts }

As a service grows, one massive OpenAPI file may become an organizational monolith.

Sometimes separate contracts are clearer:

```text
public-api.yaml
admin-api.yaml
internal-data-api.yaml
```

if they have different consumers, security requirements, or evolution cycles.

Kora can support multiple generated API contracts in one application.

The question should be architectural ownership, not merely file size.

Tags are useful for grouping operations, but a tag is not necessarily an independent contract boundary.

---

## Generated Clients Should Be Configured at Runtime { #clients-configured-runtime }

The contract defines:

```text
what operations exist
```

but deployment configuration defines:

```text
where the remote service lives
```

Those are different concerns.

The same generated client should be usable in:

```text
local
test
staging
production
```

through runtime client configuration.

Do not generate separate source code just because endpoint URLs differ.

The static protocol belongs at build time.

Environment topology belongs at runtime.

This is the same static/dynamic split that appears throughout Kora.

---

## Credentials Are Runtime State Too { #credentials-runtime-state }

OpenAPI can declare:

```text
Bearer
API key
Basic
OAuth2
```

but secrets should never be compiled into generated source.

Generation creates the typed authentication integration.

Runtime configuration, workload identity, or secret storage provides actual credentials.

Again:

```text
compile structure
keep live state dynamic
```

---

## Generator Configuration Is Part of Reproducibility { #generator-reproducibility }

The generated API depends on more than the YAML document.

It also depends on:

```text
generator version
Kora generator version
generator options
```

Those inputs can influence naming, nullability, response contracts, security integration, and generated source shape.

Therefore a reproducible API build should pin them.

The real deterministic unit is:

```text
OpenAPI contract
+
generator version
+
generator configuration
```

A generator upgrade should be treated more like a compiler upgrade than a casual plugin bump.

---

## Generated Source Is a Build Artifact and a Debugging Tool { #generated-source-debugging }

Kora's broader philosophy emphasizes readable generated source.

That is especially valuable for OpenAPI because code generation can otherwise feel like magic.

When behavior is unclear, developers should be able to inspect:

```text
generated server handler
generated model
generated client
generated response mapper
```

and follow what happens.

Generated source serves two purposes:

```text
runtime specialization
+
explanation
```

It should look boring, predictable, and mechanical.

That is a feature.

---

## Serving the Same Contract Prevents Documentation Drift { #documentation-drift }

Kora's OpenAPI management support can serve ready-made OpenAPI files and expose documentation UIs.

Architecturally, the important point is that the service can publish the same contract used for generation.

The direction remains:

```text
openapi.yaml
    ├── generates server/client code
    └── is published as documentation
```

rather than:

```text
running code
    ↓
framework tries to reconstruct OpenAPI
```

Swagger UI or another viewer becomes a presentation of the authoritative file.

Documentation cannot drift independently because it is the source.

---

## Documentation Is Only One Consumer of the Contract { #documentation-consumer }

Once OpenAPI is primary, many systems can use it:

```text
Kora server generator
Kora client generator
Swagger/Scalar UI
compatibility checker
mock server
API catalog
security scanner
contract tests
frontend code generation
mobile code generation
gateway validation
```

This is why reducing OpenAPI to "Swagger docs" wastes most of its architectural value.

The contract is a machine-readable interface definition.

Documentation is just one projection.

---

## Black-Box Tests Can Use the Generated Client { #black-box-tests }

A particularly strong pattern is:

```text
OpenAPI
   ↓
generated server
   ↓
packaged service

OpenAPI
   ↓
generated client
   ↓
black-box tests
```

Tests interact with the service through real HTTP, not direct controller calls, while still receiving compile-time types.

This gives both:

```text
production-realistic boundary
+
developer-friendly typed test code
```

The server and client share contract origin but remain separate runtime components.

---

## Still Test the Raw Protocol Where It Matters { #raw-protocol-tests }

There is one caveat.

If both generated server and generated client share the same generator defect or assumption, a test using only the generated pair could miss an interoperability problem.

Important public APIs should also include independent assertions:

- raw HTTP tests;
- schema validation;
- external client tooling;
- another language consumer where relevant.

Generation reduces accidental mismatch.

It does not remove the need to verify the actual wire.

---

## The Contract Can Drive Negative Testing { #negative-testing }

OpenAPI schemas contain useful test information.

If a field declares:

```text
minLength: 3
maxLength: 40
```

tests can exercise boundary cases.

If an operation requires bearer authentication, tests can verify unauthenticated and authenticated behavior.

If an endpoint declares `404` and `409`, tests can deliberately produce those outcomes.

The richer the contract, the more it becomes an executable test specification.

---

## Operation IDs and Schema Names Are Source APIs { #operation-ids-schema-names }

Because Kora generates source code, naming in OpenAPI matters.

Good:

```text
getUserById
CreateOrderRequest
ValidationProblem
```

Poor:

```text
usersIdGet
Request1
ErrorObject
```

A technically valid contract can still generate unpleasant APIs.

Contract designers should inspect the generated client and server interfaces and ask:

> Would I want to use this source API every day?

OpenAPI design is library design.

---

## Do Not Use Weak Schemas When the Shape Is Known { #no-weak-schemas }

A schema such as:

```yaml
type: object
additionalProperties: true
```

may be appropriate for genuinely dynamic data.

Using it simply to avoid modeling destroys much of the benefit of generation.

Likewise, representing every semantic value as a plain string weakens generated types.

If the contract knows a value is an enum, UUID, date, or structured object, express that information.

The stronger the contract, the stronger the generated source.

---

## But Do Not Leak Internal Implementation Details { #no-internal-leaks }

Strong typing does not mean exposing database design.

The fact that PostgreSQL uses a `BIGINT` column does not automatically mean the public API should expose internal storage semantics.

OpenAPI should describe consumer-relevant protocol meaning.

The contract is a boundary, not a dump of internal models.

---

## Request and Response Types Often Deserve Separation { #request-response-separation }

A common shortcut is using one schema:

```text
User
```

for create, update, and response operations.

That can produce awkward semantics.

A create request may not accept:

```text
id
createdAt
```

An update may be partial.

A response may contain derived information.

Contract-first design makes separate schemas natural:

```text
CreateUserRequest
UpdateUserRequest
UserResponse
```

The generated type system then prevents some invalid combinations automatically.

---

## Pagination, Idempotency, and Errors Are Contract-Level Decisions { #contract-level-decisions }

Cross-team API conventions should be expressed where consumers can see them.

Pagination should deliberately choose:

```text
offset/limit
cursor
page token
```

Idempotent write operations may expose an `Idempotency-Key` header.

Rate-limited APIs should declare `429` behavior and any retry hints.

These are not controller implementation details.

They are part of how consumers safely use the service.

Contract-first review helps platform teams standardize them.

---

## OpenAPI-First Does Not Mean OpenAPI for Everything { #not-everything }

Kora also supports handwritten declarative HTTP servers and clients.

That is important because not every HTTP boundary deserves code generation.

A dynamic proxy, schema-less metadata service, or tiny private endpoint may be clearer with a direct Kora HTTP abstraction.

OpenAPI-first is strongest when:

- the API is stable;
- multiple teams consume it;
- compatibility matters;
- several languages are involved;
- client generation provides real leverage.

A framework should provide a strong default without forcing the abstraction where it does not fit.

---

## OpenAPI Is Not a Domain Modeling Language { #not-domain-modeling }

The specification describes what crosses the HTTP boundary.

It should not attempt to encode the entire business architecture.

Do not move database schema, transaction rules, workflow implementation, repository design, or every business invariant into YAML.

A clean division is:

```text
OpenAPI:
external transport semantics

Generated Kora code:
transport mechanics

Domain/application:
business semantics

Runtime config:
deployment-specific facts
```

This prevents contract-first development from becoming specification-driven bureaucracy.

---

## The Generator Is a Compiler Front End { #generator-compiler-frontend }

The most useful mental model is to treat OpenAPI as a transport DSL.

Kora's generator compiles that DSL into Java/Kotlin source.

Then the normal Java/Kotlin compiler and Kora's compile-time processing continue the pipeline:

```text
OpenAPI
  ↓
Kora OpenAPI generator
  ↓
typed Java/Kotlin source
  ↓
Kora compile-time wiring
  ↓
JVM bytecode
  ↓
runtime
```

This explains why OpenAPI-first fits Kora so naturally.

Kora does not interpret the specification dynamically on every request.

It processes known structure ahead of time and produces specialized code.

The same principle appears in dependency injection, repository generation, mappings, and AOP.

---

## Runtime Becomes Deliberately Boring { #boring-runtime }

After generation, the request path is straightforward:

```text
HTTP request
    ↓
generated route/handler
    ↓
generated request mapping
    ↓
typed model
    ↓
handwritten delegate
    ↓
application service
    ↓
typed response
    ↓
generated response mapping
    ↓
HTTP response
```

The client side mirrors it:

```text
application service
    ↓
generated typed client
    ↓
generated request mapping
    ↓
Kora HTTP client
    ↓
network
    ↓
generated response/status mapping
    ↓
typed result or typed error
```

Runtime does not need to rediscover the contract.

It executes code generated from it.

Boring runtime is good runtime.

---

## A Practical Kora Workflow { #practical-workflow }

A strong Kora OpenAPI-first project can use a simple lifecycle.

First, edit:

```text
openapi.yaml
```

Define operations, schemas, declared failures, validation rules, and security.

Then run contract validation and compatibility checks.

Then generate Kora server and/or client source.

Then compile.

Then implement the generated delegate interfaces and application services.

Then run tests, including black-box tests through the network boundary.

Finally, publish the same specification through the service or API portal.

The important point is that every downstream artifact remains anchored on the same contract.

---

## The Pull Request Should Start with the Contract Diff { #pr-contract-diff }

For an API change, review order should usually be:

```text
1. What changed externally?
2. Is it compatible?
3. Is the protocol well designed?
4. Does implementation correctly realize it?
```

A contract-first pull request makes that natural.

Reviewers inspect `openapi.yaml` first.

Generated code is mechanical output.

Handwritten application changes explain how the new protocol behavior is implemented.

This is much cleaner than reconstructing API behavior from implementation changes.

---

## A Platform Team Can Turn This into a Paved Road { #paved-road }

At organizational scale, the best result is not a wiki telling teams to be contract-first.

It is tooling.

A platform Gradle convention can standardize:

```text
OpenAPI directory layout
generator version
Kora generator version
package conventions
linting
compatibility checks
generated source registration
security defaults
error conventions
contract publishing
```

Then a service team needs only to provide its contract and application behavior.

This turns architectural discipline into a default path rather than a repeated local decision.

---

## Why This Matters for CTOs and Platform Teams { #ctos-platform-teams }

The cost of an HTTP API is not the time required to write the first controller.

The long-term cost comes from:

- client duplication;
- integration bugs;
- breaking changes;
- documentation drift;
- meetings between teams;
- migrations;
- onboarding;
- version support;
- inconsistent errors and security.

Contract-first development attacks those costs structurally.

The producer and consumer no longer maintain independent interpretations of the protocol.

Kora adds another layer of leverage by turning the contract directly into framework-native typed code, so the architecture is not merely documented but compiled.

This matters increasingly as the number of services and teams grows.

---

## Why This Matters for AI-Assisted Development { #ai-assisted-development }

AI coding agents also benefit from explicit generated contracts.

Without them, an agent integrating two services may have to inspect:

- controllers;
- DTOs;
- documentation;
- exception handlers;
- security configuration;
- examples.

With OpenAPI-first development, the external interface is already concentrated in one machine-readable artifact, and the generated client exposes it as types.

The loop becomes:

```text
contract
→ generated source
→ compiler feedback
→ implementation
```

instead of:

```text
documentation prose
→ guessed HTTP code
→ runtime debugging
```

That smaller search space makes generated APIs useful not only for humans but also for automated development tooling.

---

## The Most Important Rule { #most-important-rule }

The entire approach can be summarized in one rule:

> Never hand-maintain the same protocol fact in multiple places if it can be generated from one authoritative source.

Do not independently maintain:

```text
server route
+
client route
+
documentation route
```

Do not independently maintain:

```text
server DTO
+
client DTO
+
OpenAPI schema
```

Do not independently maintain:

```text
server error mapping
+
client status switch
+
documentation error table
```

Choose the contract as the source.

Generate the projections.

For a Kora HTTP system, OpenAPI is a natural contract language.

---

## Conclusion { #conclusion }

OpenAPI becomes much more valuable when it stops being documentation generated after implementation and becomes the input from which implementation boundaries are generated.

In a code-first architecture:

```text
controller code
    ↓
framework metadata
    ↓
OpenAPI
```

the implementation owns the protocol. The specification describes what happened.

In an OpenAPI-first Kora architecture:

```text
openapi.yaml
    ↓
Kora Generator
    ↓
typed models
typed server API
typed client
typed errors
    ↓
application implementation
```

the contract owns the protocol. The server must implement it. The client is generated to consume it. Models derive from it. Status codes and error schemas become part of the typed boundary. Security
and transport validation can be generated from the same source. Documentation can publish the same file that produced the code.

This is much stronger than producing Swagger JSON.

It turns HTTP into something closer to a compiled interface between independently deployed systems.

The benefits compound over time. API design happens before implementation hardens around poor choices. Producers and consumers can work in parallel. Transport models stop drifting. Handwritten clients
disappear. Breaking changes become visible in contract diffs and can be blocked in CI. Internal refactoring no longer automatically leaks into public schemas. Errors become explicit protocol outcomes
rather than generic exceptions. Java, Kotlin, TypeScript, Go, mobile applications, gateways, tests, security tooling, and documentation can all work from one language-neutral source.

Kora is particularly well suited to this architecture because the OpenAPI generator follows the same philosophy as the rest of the framework:

```text
declare intent
→ analyze at build time
→ generate readable typed source
→ validate with the compiler
→ keep runtime thin
```

The OpenAPI generator is therefore not merely a convenience feature. It is the transport-boundary equivalent of Kora's compile-time dependency injection, generated repositories, mappings, and aspects.

The principle is the same:

> If the structure is already known before runtime, describe it once, generate the repetitive machinery, and let the compiler verify the result.

For HTTP APIs, that structure is the contract.

The contract should not be a JSON file discovered after the application has been written.

It should be the thing the application is written against.
