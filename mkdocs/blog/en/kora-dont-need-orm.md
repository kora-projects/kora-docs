---
title: Why the Kora Framework Doesn't Need an ORM for Most Services
date: 2026-09-15
description: Why a Kora Framework repository over native SQL covers most backend services better than an ORM, and when an ORM is still the right tool.
search:
  exclude: true
---

# Why Kora Doesn't Need an ORM for Most Services { #why-no-orm }

**September 15, 2026**

There is a familiar argument in Java backend development: if an application
talks to a relational database, it should probably use an ORM. The reasoning
sounds obvious. SQL is repetitive, JDBC is verbose, object mapping is
tedious, and persistence infrastructure has already been solved by mature
libraries. For a long time this made ORM-based persistence the default
choice for many server applications.

The Kora Framework takes a different position. It does not claim that ORMs are bad,
obsolete, or unnecessary in every application. It makes a narrower and more
practical argument: for a large class of backend services, the expensive
part of raw database access is not SQL itself. The expensive part is the
mechanical code around SQL. If the framework can generate that mechanical
code at compile time, then a service can keep explicit SQL and
straightforward Java or Kotlin without adopting a full object-persistence
model.

That leads to a deliberately simple equation:

```text
SQL remains SQL
Java remains Java
Kora generates glue
```

Kora repositories let the developer write a query, declare a typed
repository method, and let the framework generate the JDBC implementation,
parameter binding, row mapping, resource handling, telemetry integration,
and transaction participation. Kora 2 then combines that model with
synchronous application code and virtual threads. The result is an
architecture that looks almost old-fashioned on the surface:

```text
simple synchronous repository
+
JDBC
+
virtual threads
=
high concurrency without reactive DB API
```

But the runtime model underneath is very different from the old
platform-thread-per-request world that originally pushed many systems toward
reactive database access. Virtual threads make blocking code cheap to park.
Kora's generated repositories remove most of JDBC's repetitive ceremony. The
database connection pool remains the real concurrency boundary, where it
arguably belonged all along.

The interesting question is therefore not, "Is ORM good or bad?" The useful
question is: what problems does an ORM solve, which of those problems does
this service actually have, and which of them can be solved more cheaply
with generated repositories and explicit SQL?

For many microservices, internal APIs, event handlers, transaction-oriented
services, CRUD backends, and data-facing application components, Kora's
answer is that a full ORM often solves more problems than the service has.

## ORM Solves a Real Problem { #orm-solves-problem }

Any serious comparison should begin by giving ORM its due. Raw JDBC is
unpleasant at scale. A developer traditionally has to acquire a connection,
create a prepared statement, bind parameters using numerical indexes,
execute it, iterate a ResultSet, handle null values, map JDBC types into
application types, close resources correctly, translate exceptions,
coordinate transactions, and add instrumentation. A ten-line SQL query can
require several dozen lines of Java.

ORMs removed much of that repetitive work. They also introduced powerful
higher-level features: entity identity, persistence contexts, automatic
dirty checking, cascades, relationship navigation, lazy loading, optimistic
locking, second-level caches, query abstraction, schema mapping, and
unit-of-work semantics. In applications built around rich aggregate
persistence, these capabilities can be genuinely valuable.

The problem begins when that entire model becomes the default answer for
applications that do not actually need most of it. A service that mostly
executes explicit read projections, conditional updates, inserts, small
transactions, and a handful of database-specific queries may not benefit
from a managed object graph. It may simply need a concise way to execute SQL
safely and map results into typed values.

Kora focuses on that narrower need.

## The Fundamental Impedance Mismatch { #impedance-mismatch }

The phrase "object-relational impedance mismatch" is old, but the underlying
issue has not disappeared. A relational database represents information
using tables, rows, columns, keys, constraints, joins, sets, and declarative
queries. Java applications represent information using classes, records,
interfaces, references, collections, methods, and object identity. These are
not the same model.

A relational relationship might be expressed through a foreign key while an
object model might expose a direct reference. The difference seems small
until lifecycle enters the picture. Is the related object already loaded?
Should it be loaded immediately? Should the framework create a proxy? What
happens outside the persistence session? Does serialization trigger a query?
If the relationship changes, which SQL should be emitted? What if two object
references represent the same row? What if the request needs only three
columns but the entity contains forty?

An ORM attempts to bridge these models by creating a rich persistence layer
between them. Kora takes a different route: it does not try to make the
relational model look like an object graph. It treats the database query as
the database operation and maps the result into ordinary application values.

Instead of a pipeline where relational data becomes an ORM entity model,
then a managed graph, then application values, the common Kora path is
closer to SQL result, generated row mapper, Java or Kotlin value. The
mismatch is not "solved" by pretending the models are identical. The
boundary is made explicit and mechanically cheap.

## A Repository Does Not Need to Be an Entity Manager { #repository-not-entity-manager }

In Kora, a repository method can declare an explicit query and an ordinary
typed return value. The developer defines the database operation and the
Java-level result. The generated implementation does the boring work.

There is no requirement that the returned value be a managed persistent
object. It can be an immutable record. If code later creates another
instance with the same identifier, there is no framework-level identity map
that tries to decide whether those objects are the same persistent entity.
Creating a modified copy does not automatically update the database. The
database changes when code calls a repository operation that executes an
update.

That is a simpler semantic model: repository call equals database operation.
It replaces the more indirect relationship where object mutation,
persistence-context state, and flush timing eventually become a database
operation. For many service workloads, the explicit model is easier to
reason about.

## The Persistence Session Is Powerful but Not Free { #persistence-session }

One of the central concepts in traditional ORM architecture is the
persistence session or persistence context. It provides useful guarantees.
The framework can maintain entity identity inside the session. It can track
loaded objects, notice changes, delay SQL until flush time, batch some work,
manage relationships, and provide a unit-of-work abstraction.

This is valuable when an application genuinely wants to manipulate a
persistent object graph. But the session is also a hidden state machine. A
developer must understand whether an entity is transient, managed, detached,
or removed, and what operations move it between these states. They must
understand when SQL is emitted, what happens when a lazy relationship is
accessed after the session closes, whether a query triggers a flush, and
whether two references resolve to one managed identity.

None of these concepts are inherently bad. They are the cost of the
abstraction. The question is whether a service needs to pay that cost.

Kora repositories usually do not introduce an equivalent persistence
session. A query returns ordinary values. Those values have no hidden
database lifecycle. The connection and transaction have lifecycle; the
objects do not. For request-oriented services, this often maps more directly
to what the code is actually doing.

## Hidden Queries Are an Operational Cost { #hidden-queries }

One of the most common ORM criticisms is hidden queries. That phrase is
sometimes used unfairly, because experienced ORM users can write very
explicit queries and control fetch plans carefully. Nevertheless, the
persistence model makes it possible for database I/O to occur in places
where the source code does not visibly look like database I/O.

A property access on a related object may be a pure in-memory read or it may
trigger SQL depending on mapping and session state. The source itself does
not always tell you which. During a code review, a reviewer cannot always
determine request query count by looking for repository calls. During
serialization, traversing an object graph can accidentally initialize
relationships. During debugging, a seemingly innocent getter can become the
reason a request performs another database round trip.

With Kora's explicit repository model, database operations tend to remain
visible as repository calls, or the repository query can fetch exactly the
data the use case needs in one operation. The framework does not prevent
developers from writing too many queries. It makes those queries harder to
hide.

## The N+1 Problem Is Really a Visibility Problem { #n-plus-one-visibility }

The N+1 query problem is often presented as an ORM-specific defect. It is
not. Any application can execute one query to load N rows and then execute
another query for each row. The problem is that lazy relationship traversal
can make the additional calls less obvious.

In an explicit repository architecture, the same anti-pattern contains
visible database calls. That makes it easier to notice in code review and
easier to reason about during performance work. More importantly, Kora
encourages query-specific projections. If a use case needs user information
plus order aggregates, write the SQL that asks the database for that result
rather than reconstructing it through object navigation.

A relational database is good at joins, grouping, aggregation, and set
operations. A repository can map the result directly into a projection
designed for that use case. The query plan becomes part of the use-case
design instead of an emergent property of entity traversal.

## Query-Specific Models Reduce Impedance Instead of Hiding It { #query-specific-models }

A major source of ORM complexity is the assumption that there should be one
primary object representation of a database row. A User entity might contain
identity, profile data, relationships, permissions, audit fields, and other
state. Most queries do not need all of it.

One API endpoint may need only id and name. Another may need id and
permissions. A report may need organization and count of users. A search
result may need a joined projection from several tables. ORMs support DTO
projections and entity graphs, but the default entity-centric mental model
often encourages teams to begin from "load the entity" and optimize away
unnecessary state later.

Kora's repository model has no reason to privilege one managed entity. A
repository method can return the exact shape required by the use case: a
full value, a compact summary, a joined projection, a scalar, a boolean, or
an update count. The Java model describes what this query returns. The SQL
describes how the database computes it. Kora generates the mapping.

## Dirty Tracking Is Convenient Until You Need to Know What Writes { #dirty-tracking }

Dirty checking is one of ORM's most useful features. Within a transaction,
application code can load an entity, change a property, and rely on the
persistence provider to detect the difference and produce an update.

For domain models that naturally behave as mutable persistent aggregates,
this can make application code expressive. But dirty tracking also changes
how developers reason about side effects. A setter looks like an in-memory
mutation, yet it may imply a future database write. The actual write may
occur later during flush. Other queries may cause a flush first. Listeners
may change additional state. Optimistic versions may be updated.

Kora's explicit repository approach favors operations whose side effect is
visible. A method such as markPaid or updateEmail tells the reader that a
database change occurs. The SQL shows which columns change and can include
the concurrency condition directly. An affected-row count can expose whether
the operation actually matched the expected state.

For transaction-oriented services, that explicitness is often more valuable
than automatic dirty checking.

## Explicit Updates Can Encode Business Concurrency Better { #explicit-updates-concurrency }

Consider a state transition that is allowed only once. A generic entity
workflow may load a row, check its status, mutate it, and flush. But the
database can often express the invariant atomically in one conditional
update. If one row is affected, the transition succeeded. If zero rows are
affected, the current state was not eligible.

This removes a read-modify-write race and can avoid an unnecessary select.
Kora repositories make operations like this natural because explicit SQL is
not an escape hatch from the persistence model. It is the persistence model.

That matters for command-oriented services where many writes are best
expressed as atomic database operations rather than as object lifecycle
changes.

## The ORM Cache Is Another Layer of State { #orm-cache-state }

ORMs can maintain first-level and second-level caches. These mechanisms can
be beneficial. They can also complicate reasoning about freshness,
invalidation, memory use, and query behavior.

A service may already have Redis, Caffeine, HTTP caching, database buffer
cache, replicas, or materialized views. Adding another transparent
persistence cache is not automatically useful. For many microservices,
request lifetimes are short and caching is better expressed deliberately at
application boundaries where keys, values, TTLs, and invalidation are
visible.

Kora's repository model does not require an object cache simply to perform
data access. Caching remains a separate architectural decision rather than
an implicit property of persistence.

## Memory Overhead Is More Than Entity Objects { #memory-overhead }

The important memory difference is not that an ORM allocates objects and
JDBC does not. Both produce application data. The additional overhead comes
from the machinery required to manage entity lifecycle: persistence-context
entries, entity snapshots for dirty checking, proxy objects, lazy collection
wrappers, identity maps, metadata, and action queues.

For a small transaction, this may be irrelevant. For large result sets or
many concurrent operations, it can become more noticeable. Kora's result
model is simpler. A mapped row can become an immutable record or data class
with no attached persistence bookkeeping. Once returned, it is simply
application data.

This can reduce memory pressure and, just as importantly, reduce the number
of framework concepts attached to every database object.

## Snapshot-Based Dirty Checking Has a Cost Model { #snapshot-dirty-checking }

Traditional dirty checking often requires the framework to remember enough
previous state to know whether fields changed. That capability buys
transparent persistence. Services that mostly perform explicit updates do
not need the framework to remember old object state.

A repository operation already says what should change. No snapshot is
required to derive SQL from a later object comparison. The database
operation is known when the method is called.

This is a recurring Kora theme: avoid maintaining runtime state when
explicit operations and compile-time structure already contain the required
information.

## Session Scope Is Often Harder Than Transaction Scope { #session-scope }

A persistence session has semantics beyond the database transaction itself.
Teams have to decide whether the session is per transaction, per request, or
extended, and how lazy values behave outside that scope. Historical patterns
such as Open Session in View kept sessions alive long enough for
presentation code to access lazy relationships, but that also allowed
database I/O to occur far from the repository or service layer.

Kora's JDBC model focuses on a more concrete concept: connection and
transaction boundary. Inside a transaction, repository calls share the
transactional connection. Outside it, repository calls are independent
operations. Returned values do not need a session after the query ends.

For service applications, this lifecycle is often easier to explain.

## Transactions Should Be About Database Operations { #transactions-database-operations }

A Kora JDBC transaction can be expressed directly around operations: insert
order, insert items, insert outbox row, commit. The important fact is
visible in source: these queries share one transaction.

There is no need to reason about whether an entity is dirty, when it will
flush, or whether accessing a relationship changes the SQL sequence. The
transaction contains database actions rather than managed object state.

This model is particularly intuitive for service workflows, outbox patterns,
conditional updates, and explicit command handling.

## ORM Flush Semantics Can Surprise Otherwise Simple Code { #orm-flush-semantics }

In an ORM, a query may cause pending entity changes to flush before the
query executes so that results remain consistent with managed state. This
behavior is logical, but it means a read-looking operation can be preceded
by updates depending on earlier session activity.

Experienced ORM users understand this. The issue is not correctness. The
issue is that the source-level relationship between an operation and SQL is
indirect.

In Kora's explicit model, an update occurs because an update repository
method was called. A select occurs because a select repository method was
called. This tighter correspondence makes performance and transaction
ordering easier to inspect.

## Lazy Loading Is a Trade, Not Magic { #lazy-loading-trade }

Lazy loading solves a real problem: do not load data until it is needed. But
it does so by turning object navigation into potential I/O. A field access
can become a database operation.

For local application objects, developers generally expect property access
to be cheap and deterministic. A lazy persistence proxy changes that
expectation.

Kora prefers explicit query design for ordinary services. If an operation
needs order plus customer, write the join or projection. If it needs only
the order, do not select the customer. The query shape communicates the
fetch strategy directly. There is no separate lazy/eager configuration layer
to maintain.

## Kora Removes the Main JDBC Ergonomics Problem { #jdbc-ergonomics }

The strongest historical argument against raw JDBC is not that SQL itself is
unpleasant. It is the surrounding code: try-with-resources, prepared
statement creation, numerical parameter indexes, result-set iteration, null
conversion, type conversion, telemetry, and exception handling.

Write this hundreds of times and the project becomes a boilerplate factory.

Kora removes exactly this code through generation. The developer keeps the
parts worth reviewing: query, method signature, return type, transaction
boundary. The framework generates the ceremony.

This changes the trade-off substantially. Kora is not asking developers to
choose between Hibernate and hand-written JDBC plumbing. It offers a third
option: explicit SQL with generated execution glue.

## Generated Repositories Are Specialized Code { #generated-repositories }

At compile time, Kora knows the repository method, query text, parameter
names, parameter types, return type, row model, custom mappers, and database
component. That is enough to generate a specialized implementation.

The runtime does not need to interpret a generic repository method on every
call. Annotation processing or KSP produces ordinary Java or Kotlin
infrastructure which is then compiled with the application.

This is consistent with Kora's wider architecture. Dependency injection,
HTTP adapters, OpenAPI boundaries, repositories, mappings, and aspects all
follow the same principle: move predictable structural work to compilation
and keep runtime thin.

## Row Mapping Is Generated, Not Repeated { #row-mapping-generated }

Kora can generate row mapping for typed views such as Java records or Kotlin
data classes. Instead of reflectively discovering constructors or manually
writing result-set loops for every query, the generated mapper can directly
read columns and construct the value.

Custom mappers remain available for JSONB, arrays, enums, custom
identifiers, vendor-specific types, and other cases that need explicit
conversion.

Mapping remains a first-class concern, but it does not require a full
persistence session or runtime reflection engine.

## Query Macros Remove Structural Repetition { #query-macros }

Explicit SQL has one repetitive weakness: column lists and insert/update
field lists can become tedious to maintain. Kora query macros target exactly
this problem.

A select macro can derive the fields of a return view. An insert macro can
derive the columns and named parameters of an input view. Identifier-aware
macros can exclude generated IDs or build predicates.

The important point is what macros do not do. They do not replace SQL with a
framework query language. They remove mechanical fragments while preserving
joins, filters, grouping, ordering, locking, CTEs, and vendor syntax in
plain SQL.

That is a narrow abstraction with a small semantic gap.

## SQL Visibility Shortens Performance Debugging { #sql-visibility }

When a Kora repository is slow, the debugging sequence is direct: identify
the repository method, read the SQL, run EXPLAIN or EXPLAIN ANALYZE, inspect
indexes and row estimates, then change query or schema.

With a more abstract persistence layer, the sequence may include determining
generated SQL, fetch plan, flush behavior, and actual query count before the
database investigation even begins.

Good ORM tooling can make those steps manageable. Kora simply removes them
from the default path.

For teams that own database performance, this transparency is often a major
advantage.

## Native Database Features Stop Being Escape Hatches { #native-database-features }

Relational databases provide powerful capabilities that do not map neatly to
a universal object model. PostgreSQL offers RETURNING, ON CONFLICT, JSONB,
arrays, window functions, CTEs, SKIP LOCKED, advisory locks, and specialized
operators.

ORMs support many vendor features through provider-specific mechanisms or
native queries. In Kora, using those features does not mean leaving the
intended persistence model. The intended model already starts with native
SQL.

A work-claim query can use SKIP LOCKED directly. An upsert can use ON
CONFLICT. An update can use RETURNING. The framework does not need to invent
an intermediate abstraction for every database feature before the
application can use it.

## Database Portability Is Usually Overestimated { #database-portability }

There are systems where supporting multiple relational databases is a
genuine product requirement. In those systems, a portable abstraction can
have real value.

Many production services, however, are not realistically portable at the
database level. They depend on migrations, data types, indexes, query plans,
locking behavior, extensions, replication, and operational tooling. Moving
from PostgreSQL to another database is usually an architectural migration,
not a connection-string change.

If portability is not a real requirement, avoiding database-specific
capabilities merely to preserve theoretical flexibility can impose real cost
for hypothetical benefit.

Kora keeps the database visible and lets teams decide how portable they
actually need to be.

## One Repository Model Does Not Mean One Database Abstraction { #one-repository-model }

Kora provides a common repository programming model for JDBC and Cassandra,
but it does not pretend those databases are interchangeable.

The shared concepts are repository, query, typed parameters, typed results,
mapping, batching, and telemetry. The implementation semantics remain
native.

JDBC has SQL, connections, prepared statements, result sets, transactions,
and generated keys. Cassandra has CQL, CqlSession, bound statements,
partition-aware data modeling, execution profiles, and Cassandra-specific
consistency semantics.

This is the right level of abstraction: unify developer mechanics, preserve
technology reality.

## Cassandra Shows Why ORM Thinking Does Not Generalize { #cassandra-orm-thinking }

Cassandra tables are designed around access patterns. Denormalization is
normal. Partition keys and clustering keys determine query viability.
Cross-table joins are not the central model.

A query-centric repository model fits naturally because Kora does not
require a relational entity graph underneath. The developer writes CQL,
declares a typed method, and Kora generates binding and row mapping.

The same ergonomics survive. The database semantics do not get erased.

## Most Services Do Not Need One Canonical Entity Type { #canonical-entity-type }

Without a persistence context, there is no pressure to make one class serve
every database use case.

A service can have UserRow, UserSummary, UserCredentials, UserSearchResult,
CreateUser, UpdateUserEmail, and other purpose-built types. These are not
necessarily redundant. They represent different contracts.

A search result may combine several tables. A summary may contain two
columns. A create command may omit a database-generated identifier. A write
may return only an update count.

This projection-first style often produces code closer to the actual use
cases than one canonical entity graph.

## Memory Use Becomes Easier to Control { #memory-use-control }

Query-specific projections help memory behavior. If an endpoint needs three
columns, it can select and materialize three columns. It does not need to
load a full entity with twenty fields or create lazy proxies for
relationships it probably will not access.

This does not guarantee low memory; an explicit SQL service can still load
enormous result sets carelessly. The advantage is that the framework does
not impose a larger object graph than the query requested.

Memory stays closer to the explicit data-access design.

## The Second-Level Cache Is Not Automatically a Feature { #second-level-cache }

Caching should answer a specific consistency and performance problem. A
service may choose Redis, Caffeine, HTTP caching, materialized views, or
database replicas depending on the use case.

An ORM second-level cache can be powerful, but it also creates another
invalidation domain. When the service already uses explicit business read
models, an application-level cache may be easier to define and observe.

Kora keeps caching and persistence as separate concerns. The service adds a
cache because a use case benefits from one, not because entity persistence
brings a cache subsystem with it.

## Simple Values Are Easier to Serialize { #simple-values-serialize }

Managed ORM entities can contain lazy relationships or runtime proxies whose
behavior depends on session state. Serializing them directly through an HTTP
API can trigger extra queries, expose internal relationships, recurse
unexpectedly, or fail after session closure.

Mature ORM applications often solve this by introducing DTOs anyway.

Kora repository results are already ordinary values. They can be
query-specific records or mapped into OpenAPI-generated response models. The
HTTP contract and persistence contract remain separate.

This fits Kora's broader contract-first philosophy.

## Explicit SQL Does Not Mean Database Schema Dictates Java { #explicit-sql-schema }

Kora mapping supports column naming overrides, embedded values, custom
mappers, and typed wrappers. Java and Kotlin can still use meaningful value
objects rather than mechanically mirroring table columns.

The database model and application model are allowed to differ. Kora simply
generates the bridge instead of maintaining a persistent managed-object
state machine around the application model.

This is an important distinction: rejecting ORM does not mean rejecting
mapping or domain design.

## Virtual Threads Change the Historical JDBC Trade-Off { #virtual-threads-jdbc }

The most important Kora 2 connection is virtual threads.

Why did reactive database access become attractive? One major reason was the
cost of blocking platform threads. Traditional server architecture tied a
request to an operating-system-backed Java thread. When that thread executed
JDBC and waited for the database, the thread remained unavailable for other
work.

At thousands or tens of thousands of concurrent I/O waits, platform-thread
stacks and scheduler overhead became expensive. Reactive architectures
addressed this by representing asynchronous work without dedicating one
heavyweight thread to each waiting request.

That was a real engineering problem.

Virtual threads change that particular constraint.

## Virtual Threads Make Blocking Cheap to Park { #virtual-threads-blocking }

A virtual thread is still a Java Thread from the application's perspective,
but it is not permanently tied to one carrier thread. During supported
blocking I/O, the JVM can park the virtual thread and let the carrier
execute another task.

Application code can therefore remain straightforward: call repository, wait
for result, continue. While the JDBC operation waits, the virtual thread can
be parked. The carrier is free to run other virtual threads.

This restores the ergonomic value of thread-per-request programming without
requiring one heavyweight platform thread for every in-flight request.

That is the foundation of Kora 2's synchronous direction.

## Blocking a Virtual Thread Is Not the Same as Blocking a Carrier { #blocking-virtual-thread }

The desired behavior is virtual thread waits, carrier becomes available.
This is fundamentally different from the historical model where the
request's platform thread waited and remained unavailable.

However, some operations can pin virtual threads to carriers, and native
code or synchronization patterns can affect behavior. Libraries still need
production validation.

Virtual threads reduce the cost of waiting. They do not make every form of
blocking universally free.

## JDBC Is Naturally Compatible with the Synchronous Model { #jdbc-synchronous }

JDBC is synchronous: execute query, wait, receive result. This historically
created tension with event-loop servers because calling JDBC directly on an
event-loop thread would stop unrelated work.

The traditional solutions were to offload JDBC to a worker pool or use a
reactive database driver.

Virtual threads introduce another option: execute application code on a
virtual thread, call ordinary JDBC, and let the virtual thread park during
I/O.

This aligns extremely well with Kora's repository API. Repository signatures
remain synchronous. Database drivers remain mature JDBC drivers. Application
control flow remains ordinary Java or Kotlin. Concurrency scales through
virtual threads rather than through reactive return types.

## Simple Synchronous Repository + JDBC + Virtual Threads { #synchronous-repository-jdbc }

The architecture can be summarized directly:

```text
simple synchronous repository
+
JDBC
+
virtual threads
=
high concurrency without reactive DB API
```

Each part matters. A simple synchronous repository gives callers ordinary
values rather than publishers or futures. JDBC provides the mature
relational Java ecosystem. Virtual threads mean waiting on JDBC no longer
requires dedicating a heavyweight platform thread for the entire wait.

Together, these properties remove much of the historical motivation for
introducing reactive database APIs into ordinary request-response services.

## Reactive Database APIs Still Have Legitimate Uses { #reactive-database-apis }

Reactive database access is not obsolete. It remains valuable for workloads
built around end-to-end streaming, explicit backpressure, reactive
composition across asynchronous systems, or libraries and drivers whose
reactive semantics provide real value.

The argument is narrower: a service should not need a reactive database API
*only* because blocking a platform thread was too expensive.

Virtual threads change that cost. If the application naturally fits
synchronous request-response and transaction flow, JDBC becomes attractive
again at concurrency levels that once pushed teams toward reactive
programming.

## Reactive Complexity Is an Engineering Cost { #reactive-complexity }

Reactive APIs change application structure. Instead of straightforward
sequential control flow, developers work with operators, subscriptions,
scheduler boundaries, context propagation, cancellation, backpressure, and
asynchronous stack traces.

Experienced reactive teams can handle this well. If the workload genuinely
benefits from reactive semantics, the complexity is justified.

If the only goal is avoiding blocked platform threads, virtual threads
provide a much simpler answer. Kora 2 deliberately prefers that simpler
model for the common path.

## Transaction Code Is Easier to Read Synchronously { #transaction-code-synchronous }

Transactions often contain dependent steps: insert order, use generated
identifier, insert items, insert outbox event, return result.

Synchronous code expresses this naturally inside one transaction block. With
reactive database access, transaction context must flow through asynchronous
composition correctly. Libraries support this, but the mental model is
larger.

Virtual threads make synchronous transaction code scalable without forcing
the transaction itself into a reactive graph.

For business services where transaction boundaries are central to
correctness, this simplicity matters.

## The Database Connection Pool Is Still the Real Limit { #connection-pool-limit }

Virtual threads can create enormous concurrency. A database cannot
necessarily handle enormous concurrency.

A service might have tens of thousands of virtual threads but only a few
dozen JDBC connections. Only those connections can actively run database
operations at once. The remaining tasks wait for the pool.

This is not a failure. It is the intended resource boundary. The database
has finite CPU, memory, locks, storage throughput, and connection capacity.

Virtual threads remove the application-thread bottleneck while preserving
the database-resource bottleneck. That makes the connection pool's role
clearer.

## Unlimited Virtual Threads Do Not Mean Unlimited Database Concurrency { #unlimited-virtual-threads }

Virtual threads make waiting cheap; they do not make the resource being
waited for unlimited.

Database throughput is still determined by pool size, query latency,
transaction duration, lock contention, storage, CPU, and network. If arrival
rate exceeds service capacity, waiting virtual threads can accumulate.
Memory is cheaper than platform-thread stacks, but queued requests still
retain request state and increase latency.

The system still needs timeouts, load shedding, capacity planning, and
sensible retry policy.

Virtual threads simplify concurrency mechanics. They do not repeal queueing
theory.

## Little's Law Still Applies { #littles-law }

For a stable system, concurrency is approximately throughput multiplied by
latency. If latency increases under overload, the same throughput requires
more concurrency, which can increase queueing and pressure further.

Virtual threads make it easier for the application to hold many waiting
operations. They do not make that system healthy.

This is why Kora's synchronous model should be paired with production
capacity planning rather than interpreted as "blocking is free."

## The Pool Becomes an Explicit Backpressure Boundary { #pool-backpressure }

A bounded JDBC connection pool naturally limits the number of database
operations executing concurrently. Many request virtual threads may exist,
but only a controlled number obtain database connections.

This protects the database only if waiting itself is bounded and observable.
A healthy service needs connection-acquisition timeouts, request timeouts,
pool saturation metrics, and latency SLOs.

The simplicity of synchronous code does not remove the need for operational
controls.

## Do Not Hold a Database Connection While Waiting on the Network { #hold-connection-network }

Virtual threads make remote waiting cheap for Java, but database connections
remain scarce. A transaction that performs a database update, then waits on
a remote HTTP call, then performs another database update can hold
connections and locks while doing no database work.

The virtual thread may park efficiently. The database resources do not.

This is where patterns such as outbox, saga, idempotent workflow, or
transaction-then-remote-call matter. Virtual threads optimize thread
scheduling, not distributed transaction design.

## Long Transactions Are Still Long Transactions { #long-transactions }

The same applies to expensive application computation inside a transaction.
If a transaction opens, performs one query, spends seconds doing CPU work,
and then issues another query, the database connection remains occupied
unnecessarily.

Kora's explicit transaction scope makes this easier to see in review. The
rule remains simple: keep database transactions as small as correctness
allows.

## The Return of JDBC Is Really the Return of Straight-Line Code { #return-of-jdbc }

The point is not nostalgia for JDBC. Nobody wants thousands of hand-written
result-set loops.

The attractive combination is mature JDBC drivers, generated repository
boilerplate, virtual-thread concurrency, integrated telemetry, and
straight-line application code.

Kora's compiler removes the old JDBC ergonomics problem. Loom removes much
of the old thread-scalability problem. What remains is the native database
model, which production engineers had to understand anyway.

That is why Kora can build a modern high-performance backend around a
programming style that looks simple.

## The Reactive Era Solved a Real Historical Constraint { #reactive-era }

Reactive server architectures were not invented because developers wanted
complexity. They addressed real platform limitations. When requests consumed
heavyweight threads and services spent most of their time waiting on
databases or remote APIs, thread counts became expensive.

Asynchronous and event-driven runtimes could multiplex huge numbers of I/O
waits over small thread pools. Reactive libraries added composition and
backpressure semantics.

This was a rational response to the platform available at the time.

Virtual threads do not prove reactive architecture was a mistake. They
change the assumptions under which teams make the choice today.

## Kora 2 Can Prefer Synchronous APIs Without Going Backward { #kora2-synchronous-apis }

Kora 2's synchronous-first model should not be read as "blocking won." A
better interpretation is that the JVM changed enough that blocking-looking
source code no longer implies one heavyweight blocked operating-system
thread.

The source model and runtime model have decoupled. Application code can look
sequential while the JVM schedules huge numbers of virtual threads over a
smaller number of carriers.

That lets framework designers recover familiar APIs without sacrificing I/O
concurrency. Kora takes that opportunity aggressively.

## Synchronous Signatures Improve API Locality { #synchronous-signatures }

A repository method returning a User says exactly what the caller needs to
know. The caller receives a value. The exception model is ordinary. The
stack trace follows ordinary calls. The transaction can be represented by
normal lexical scope.

A reactive return type communicates additional execution semantics that can
be useful, but those semantics propagate through callers. If the service
does not need streaming or explicit asynchronous composition at that
boundary, the synchronous signature has lower cognitive overhead.

Virtual threads make that lower-overhead signature viable at high
concurrency.

## Debugging Becomes More Familiar { #debugging-familiar }

Straight-line synchronous calls generally produce stack traces that match
source structure more closely. During an incident, an engineer can often see
controller, service, repository, JDBC.

Reactive tooling has improved substantially, but asynchronous execution
still introduces different debugging patterns.

For platform teams with many ordinary Java developers, familiar debugging
has economic value. A simpler model reduces training and incident-diagnosis
cost.

## Mature JDBC Drivers Are a Major Asset { #mature-jdbc-drivers }

JDBC represents decades of engineering across database vendors. Drivers have
mature support for authentication, prepared statements, batching, generated
keys, database-specific types, TLS, failover options, observability
integrations, and connection pools.

Reactive drivers have improved significantly, but choosing JDBC gives teams
the most established path for many relational databases.

If virtual threads remove the thread-scalability reason to avoid JDBC, that
ecosystem maturity becomes a major advantage.

Kora's repository layer lets teams benefit from it without accepting raw
JDBC boilerplate.

## JDBC Transactions Are Widely Understood { #jdbc-transactions }

Experienced Java backend engineers already understand connection,
auto-commit, commit, rollback, and isolation. This knowledge transfers
across frameworks.

An explicit Kora transaction sits close to these semantics. That reduces the
amount of framework-specific knowledge required to reason about atomicity.

A CTO or platform team should care about this because transferable knowledge
improves onboarding and team mobility.

## An ORM Adds a Second Optimization Layer { #orm-optimization-layer }

When an ORM application is slow, there are at least two optimization
domains: ORM behavior and database behavior.

An engineer may need to tune fetch strategy, entity graph, batch size,
persistence-context scope, flush mode, or cache behavior, and then still
tune SQL, indexes, statistics, and schema.

With Kora repositories, most performance work begins directly in the
database domain. There is still framework configuration, pool sizing, and
mapping, but the semantic gap is smaller.

For platform teams trying to standardize performance practices, fewer layers
can be a meaningful advantage.

## Explicit Caching Gives More Deliberate SLOs { #explicit-caching-slos }

Suppose product data is cached for five minutes. An application-level cache
can state the key, value, TTL, and invalidation behavior clearly.

If the repository remains deterministic, the cache boundary can be tested
independently. This is often preferable to relying on persistence-level
caching semantics optimized around entities rather than business read
models.

Kora has dedicated cache abstractions, so caching can be added where the use
case benefits rather than bundled with the persistence model.

## ORM Entity Graphs Can Grow Beyond the Request { #orm-entity-graphs }

Object graphs are convenient because related data feels naturally navigable.
They can also make it easy to load more data than the request needs.

A user has orders, orders have items, items have products, products have
categories. The application eventually needs a fetch strategy to decide how
far traversal goes.

Kora starts from the query result. If an endpoint needs three joined values,
select three joined values. The database is already good at constructing
relational projections. There is no need to recreate an entire relationship
graph in memory first.

## Reporting and Aggregation Rarely Need Managed Entities { #reporting-aggregation }

Reports commonly need SUM, COUNT, GROUP BY, window functions, several joins,
and date bucketing. The result may have no meaningful entity representation.

Kora can map an aggregation query directly into a purpose-built record. No
persistent identity or object lifecycle is required.

This is one reason read-heavy services often gain little from full ORM
semantics.

## Search Is the Same Story { #search-same-story }

Search endpoints often return a compact projection assembled from several
sources: id, display title, owner, status, matched snippet.

Treating this as a managed entity graph adds little. A query projection is
the natural representation.

Kora's compile-time mapping makes this cheap.

## Read and Write Models Can Diverge Cleanly { #read-write-models }

A service may write through compact command queries and read through
optimized projections. There is no requirement that both operations share
one entity class.

This is compatible with CQRS-style thinking without requiring a heavyweight
CQRS framework. Repository APIs simply reflect the actual use cases.

## Most Services Are More Transaction-Script-Like Than They Admit { #transaction-script-like }

A large number of microservices have application flows resembling: validate
request, read several rows, apply rule, write one or several rows, write
outbox event, return response.

That is closer to an application service or transaction script than to
manipulation of a long-lived persistent object graph.

A service like this may use ORM entities because ORM is the organizational
default, not because the workload benefits from persistence-context
semantics.

For these applications, Kora repositories can remove substantial conceptual
machinery without making database code verbose.

## CRUD Is Not an Argument for ORM by Itself { #crud-not-orm-argument }

Basic CRUD is easy for almost every persistence technology. With Kora macros
and generated mappers, CRUD repositories can remain concise while keeping
SQL explicit.

If a service needs simple CRUD plus a few custom queries, introducing
persistence sessions, dirty tracking, lazy relationships, and cache
semantics may be more abstraction than the problem requires.

## Bulk Updates Are Natural Without Entity Materialization { #bulk-updates }

Suppose a service must expire all sessions older than a timestamp. The
natural database operation is one update over a set.

An entity-oriented model can perform bulk operations too, but the operation
does not conceptually need to load objects.

Kora makes set-based SQL first-class. The database performs the work. Java
receives an update count.

This is often simpler and more efficient.

## Set-Based Thinking Is an Important Database Skill { #set-based-thinking }

Relational databases are optimized for set operations. Object-oriented code
naturally encourages iteration over objects.

ORMs bridge the two, but explicit SQL keeps set-based thinking close to
application design.

Before launching many individual operations, ask whether the database can
perform one join, batch, aggregation, or conditional update instead.

This mindset matters more than the persistence framework itself.

## Virtual Threads Can Make Bad Database Patterns Fail Faster { #virtual-threads-bad-patterns }

Because virtual threads make concurrency cheap, teams can accidentally
parallelize inefficient patterns. Launching one virtual thread per item does
not make a hundred database round trips a good idea.

The database still receives a hundred operations. Across many requests, the
pool becomes saturated.

Use set-based SQL, batch APIs, or better query design before using
concurrency to mask a poor access pattern.

Virtual threads make legitimate concurrency cheap. They do not make
inefficient database work efficient.

## Batch APIs Still Matter { #batch-apis }

For repeated inserts or updates, a generated batch repository method can
reduce round trips and driver overhead. This is often preferable to one
concurrent insert per row.

Again, database-native bulk mechanisms should be used before
application-level concurrency.

Kora supports batching while keeping the query explicit.

## Optimistic Locking Does Not Require a Managed Entity { #optimistic-locking }

Optimistic locking is often associated with an entity version field, but the
underlying mechanism is a conditional update.

A repository can update a row where id and expected version match, increment
the version, and inspect affected-row count. Zero rows means concurrent
modification.

This is explicit, works naturally with immutable values, and does not
require persistence lifecycle state.

An ORM annotation is convenient; it is not the only implementation of
optimistic concurrency.

## Pessimistic Locking Is More Transparent in SQL { #pessimistic-locking }

Similarly, a database-specific locking clause can be written directly. Teams
do not need to remember which ORM lock mode maps to which database behavior.

For services intentionally standardized on one database engine, native SQL
often communicates the concurrency mechanism more clearly.

## The Outbox Pattern Fits Explicit Repositories Naturally { #outbox-pattern }

A reliable event-publication flow often needs to update business state and
insert an outbox record in one transaction. With Kora, both operations can
be explicit repository calls inside one JDBC transaction.

There is no hidden entity flush ordering to reason about. The atomicity is
defined around database operations directly.

This is an excellent example of how simple synchronous repositories compose
with distributed-system patterns.

## Virtual Threads Do Not Fix Distributed Transactions { #virtual-threads-distributed }

A transaction that holds a database connection while waiting for another
service is still risky. The virtual thread may park cheaply, but locks and
connections remain occupied.

Distributed workflows still need architecture: outbox, saga, idempotency,
compensation, or another appropriate pattern.

Kora's simpler programming model should not be confused with simpler
distributed-systems requirements.

## Query Count Becomes a Reviewable Metric { #query-count-metric }

Because database access maps closely to repository calls, teams can create
straightforward performance expectations: this endpoint should execute one
repository call; this workflow should execute no query per item; this batch
path should remain bounded.

Telemetry can use stable repository operation names, making source and
production measurements easier to correlate.

This is another operational benefit of a thin data layer.

## Telemetry Belongs in Generated Glue { #telemetry-generated-glue }

Hand-written JDBC often starts without consistent tracing and metrics.
Kora's database infrastructure can integrate telemetry into generated
repository calls.

This is exactly the kind of cross-cutting concern generation should own. The
developer writes the query. The platform receives standardized
instrumentation.

A complex manual query can still remain inside the same telemetry
infrastructure rather than disappearing from observability simply because it
needed an escape hatch.

## A Good Abstraction Has an Escape Hatch { #abstraction-escape-hatch }

No declarative repository model covers every query elegantly. Dynamic search
filters, unusual driver APIs, database-specific features, and specialized
streaming can require manual code.

Kora lets repository code drop down to connection-level control when
necessary without abandoning the framework's transaction and telemetry
infrastructure.

This layered escape path is important: generated query first, custom mapper
if needed, manual query if needed, direct driver behavior where genuinely
necessary.

A framework that has no escape hatch eventually becomes a framework
developers fight.

## Native Queries Are Not a Failure Mode in Kora { #native-queries }

In ORM projects, teams sometimes say they had to fall back to native SQL.
That wording reveals the abstraction hierarchy: SQL sits below the preferred
model.

In Kora, SQL is the preferred model for JDBC repositories. Using
PostgreSQL-specific syntax is not leaving the framework. It is using the
database intentionally.

That cultural difference affects how teams design and optimize persistence.

## Repository Results Are Plain Values { #repository-plain-values }

A repository result can be a record, data class, scalar, list, nullable
value, or query-specific projection. It does not carry a hidden persistence
lifecycle.

This makes values easier to pass across application layers and safer to use
in concurrent request processing. There is no temptation to store a managed
entity in a cache and later discover it is detached or tied to another
session.

Plain values fit virtual-thread-per-task architectures naturally.

## Immutable Models Fit Especially Well { #immutable-models }

Java records and Kotlin data classes are natural database projections. A
generated mapper constructs them once. They can move through the application
without persistence callbacks or hidden mutation tracking.

This encourages a value-oriented style: query result, immutable value,
business computation.

For concurrent services, fewer hidden mutations often make code easier to
reason about.

## Nullability Should Follow the Query, Not a Canonical Entity { #nullability-follow-query }

A table column may be non-null, but an outer join can make the projection
nullable. A table may have a nullable column that one query filters to
non-null.

Projection-oriented repositories let the result type model the query's
actual null semantics instead of copying one entity definition mechanically
everywhere.

Kotlin's nullability model is particularly useful here.

## Multiple Databases Stay Explicit in the Application Graph { #multiple-databases }

If a service talks to multiple databases, Kora can distinguish database
components and wire repositories to the correct connection infrastructure
through the compile-time graph.

The topology remains visible. There is no requirement for an implicit
primary persistence context that every repository silently uses.

This matters in systems where database ownership and routing are
architectural concerns.

## Database Access Is Not a Separate Framework Universe { #database-access-framework }

Some stacks have one container for application dependencies and another
conceptual subsystem for persistence-managed objects.

Kora keeps repositories inside the same component graph as controllers,
services, clients, configuration, and telemetry.

The database is special because databases are special, not because the
framework creates an additional object-management universe around them.

## Fewer Runtime Containers Mean Fewer Mental Models { #fewer-runtime-containers }

A developer does not need to reason simultaneously about dependency
injection state, persistence session state, runtime repository proxies, and
entity lifecycle to understand a basic query.

The repository is a generated component with explicit dependencies.

This reduction in mental models is one of Kora's broader design goals.

## ORMs Can Be Highly Performant { #orms-highly-performant }

None of this means ORM is inherently slow. A well-designed Hibernate
application with appropriate projections, fetch plans, batching, caching,
indexes, and SQL knowledge can perform extremely well.

The argument is about complexity per capability, not raw benchmark morality.

If a team needs the ORM capabilities and knows how to operate them, the
abstraction cost may be entirely justified.

## Most ORM Problems Are Manageable with Expertise { #orm-problems-expertise }

N+1 can be solved. Lazy loading can be controlled. Fetch plans can be
explicit. Caches can be configured. Sessions can be scoped. SQL can be
logged and profiled.

The provocative question is simply whether most services should require that
expertise in the first place when their persistence needs are narrower.

Kora's answer is often no.

## The Smaller Model Can Be a Better Default { #smaller-model-default }

A new Kora service can begin with typed repository, explicit query,
generated mapper, explicit transaction, JDBC, and virtual threads.

If richer entity lifecycle semantics later become clearly valuable, the team
can evaluate an ORM deliberately.

Starting with the smaller model reduces upfront complexity and makes the
addition of more powerful abstractions a conscious choice rather than
inherited convention.

## The Best Architecture Is Often the One with Fewer Hidden State Machines { #fewer-hidden-state-machines }

A backend already contains many state machines: HTTP connections,
transactions, locks, retries, circuit breakers, message offsets, business
workflows.

A persistence session adds managed/detached state, dirty tracking, flush
rules, and proxies. A reactive pipeline adds subscription, scheduler,
context, and backpressure state.

Both can be justified. Neither should be added casually.

Kora's default path aims for fewer hidden state machines: call method,
execute query, return value; virtual thread blocks, JVM parks it, resume
when ready.

That simplicity is strategically valuable.

## The Modern Stack Changes the Historical Default { #modern-stack-default }

Twenty years ago, the trade-offs looked different. Raw JDBC was extremely
verbose. Platform threads were expensive at high concurrency. Runtime
reflection was common.

Today Kora can combine compile-time generation, records and data classes,
generated repositories, generated JSON, virtual threads, modern JDBC
drivers, and fast integration tests.

That changes what "simple database access" can mean.

It is reasonable to revisit defaults created under older platform
constraints.

## The Right Question for a New Service { #right-question-new-service }

For a new Kora service, ask: do we need object persistence semantics, or do
we need convenient database access?

If the answer is convenient database access, generated repositories are
usually the smaller solution.

If the answer genuinely includes managed aggregate lifecycle, relationship
navigation, extensive dirty tracking, identity semantics, and
persistence-session behavior, an ORM may be appropriate.

Do not introduce a persistence session merely to avoid writing SELECT. Kora
already makes SELECT cheap.

## A Practical Decision Checklist { #decision-checklist }

A service probably does not need a full ORM if queries are already important
to application design, read models differ by use case, writes are explicit
commands or conditional updates, transactions are small and deliberate,
database-specific SQL features matter, lazy relationship navigation is not
central, immutable values are desirable, JDBC meets database needs, and
virtual threads provide the required concurrency model.

A service may benefit from ORM if rich aggregate graphs are central,
unit-of-work and dirty tracking materially simplify the code, relationship
navigation is genuinely useful, or the organization already has deep ORM
expertise and conventions that outweigh the additional model complexity.

This is not a moral choice. It is an architectural fit question.

## A Kora Request Path with JDBC and Virtual Threads { #kora-request-path }

The request lifecycle is straightforward:

```text
socket
  ↓
Undertow network processing
  ↓
Kora application handler
  ↓
virtual thread
  ↓
service
  ↓
generated repository
  ↓
JDBC connection pool
  ↓
database
```

When JDBC waits on network I/O, the virtual thread can park. The carrier can
execute other work. When the database responds, the virtual thread resumes
and continues the ordinary call stack.

This is the programming model Kora wants developers to see.

## Where the Concurrency Limit Actually Lives { #concurrency-limit }

Several resources have different roles. The HTTP server can maintain many
connections. Virtual threads can represent many concurrent requests cheaply.
Carrier threads execute runnable virtual threads. The JDBC pool bounds
concurrent database use. The database bounds actual query execution.

The useful hierarchy is many requests, many virtual threads, bounded
database connections, finite database execution capacity.

Understanding this hierarchy is more useful than simply saying virtual
threads scale.

## Why a Reactive Driver May Not Improve a Pool-Bound Service { #reactive-driver-pool }

Suppose the database can productively process only a certain number of
concurrent queries. A reactive driver can represent many waiting operations
efficiently. Virtual threads can also represent many waiting operations
efficiently.

Neither changes the database's useful capacity.

If the service's primary reason for reactive adoption was thread cost,
virtual threads remove much of that advantage. The remaining comparison
should be about streaming, backpressure, driver capabilities, composition,
and operational behavior.

That is a more honest decision basis.

## Synchronous Code Can Still Use Bulkheads { #synchronous-bulkheads }

A virtual-thread service should not allow every incoming request to queue
indefinitely for an expensive database operation.

Bulkheads, semaphores, pool limits, timeouts, and load shedding can cap
specific work even when global request concurrency is high.

Reactive architecture does not have a monopoly on bounded concurrency. The
mechanism is simply different.

## Transaction Isolation Still Matters Exactly as Before { #transaction-isolation }

Virtual threads do not change READ COMMITTED, REPEATABLE READ, SERIALIZABLE,
phantom behavior, write skew, or deadlocks.

Kora's explicit JDBC approach may actually make it easier to remember that
transaction correctness belongs to the database. The programming model
changed. Database theory did not.

## Connection Pool Timeouts Become Part of the Request SLO { #connection-pool-timeouts }

If a request waits hundreds of milliseconds for a connection before
executing a fast query, user latency is already poor.

A virtual thread will wait efficiently, which means the application can look
healthy from a thread perspective while queueing is already violating the
SLO.

Metrics must separate pool acquisition from query execution.

Cheap parking must not hide overload.

## Virtual Threads Can Hide Overload Longer { #virtual-threads-overload }

A platform-thread service might visibly exhaust a worker pool during
overload. A virtual-thread service can represent many more queued requests
before thread count becomes the obvious failure.

This is good when load is transient. It is dangerous if it encourages
unbounded queues.

Systems need explicit overload indicators: pool wait, latency, memory,
request timeout rate, database saturation.

Kora's simplicity should be paired with disciplined operational budgets.

## N+1 with Virtual Threads Is Still N+1 { #n-plus-one-virtual-threads }

Launching many virtual threads can reduce wall-clock latency for independent
calls, but it does not reduce query count or database work.

If one request fans out a hundred database queries, the database still sees
a hundred operations. Across many requests, this can overwhelm the pool.

The correct optimization is often one set-based query.

Virtual threads make concurrency cheap. They do not make inefficient access
patterns efficient.

## The Best Database Operation Is Often the One You Do Not Execute { #best-database-operation }

Explicit repositories make it natural to optimize query count. Instead of
load entity then lazily access three relationships, design one projection.
Instead of check then update, use a conditional update. Instead of insert
one row at a time, batch. Instead of query each item, use a join, IN
strategy, or another database-native technique.

These optimizations often dwarf framework overhead.

Kora's data-access model keeps them visible.

## ORM Plus Virtual Threads Is Also Possible { #orm-plus-virtual-threads }

Virtual threads are not exclusive to Kora repositories. Hibernate and other
ORM-based applications can also benefit from them, subject to library and
connection-pool behavior.

Kora's distinctive choice is to combine two independent simplifications: no
persistence session unless needed, and no reactive database API unless
needed.

Together they create a particularly transparent stack.

## Why Kora's Choice Is Stronger Than Merely Using a JDBC Helper { #kora-jdbc-helper }

Java has had JDBC helper libraries for years. Kora adds a framework-wide
compile-time model: repositories are generated, mappings are generated, DI
is compile-time, HTTP adapters are generated, OpenAPI contracts can generate
boundaries, and virtual threads support synchronous service flow.

The significance is not one helper API. It is the consistency of the
architecture.

Most structural adaptation happens before runtime. Application code stays
close to underlying technologies.

## The Repository Model Complements OpenAPI-First Development { #repository-openapi }

At the HTTP boundary, an OpenAPI contract can generate typed server and
client code. At the database boundary, SQL plus a repository signature
generates the JDBC adapter.

The service sits between two explicit contracts.

The architecture becomes: external protocol explicit, business logic
explicit, database operation explicit, framework glue generated.

Very little important behavior is hidden in runtime convention.

This is a distinctive Kora design strength.

## Thin Boundaries Reduce Semantic Translation { #thin-boundaries }

A deep stack can look like HTTP abstraction, service abstraction, ORM
abstraction, driver, database.

Kora aims for generated HTTP adapter, application code, generated repository
adapter, JDBC, database.

Each boundary is relatively thin. The request-to-SQL path is easier to
trace.

That is valuable for performance, debugging, onboarding, and AI-assisted
development.

## AI Agents Benefit from Explicit Data Access { #ai-agents-data-access }

A coding agent can inspect repository method, SQL, model, migration, and
generated implementation. It does not have to reconstruct hidden
persistence-context state, lazy relationship rules, proxy behavior, or flush
semantics before understanding a query.

If a mapper is missing, compilation can fail. If the SQL is wrong against
the schema, an integration test can fail.

This creates a tight and relatively deterministic feedback loop.

## SQL Is Shared Technical Language for Humans and Agents { #sql-shared-language }

A query communicates database intent directly. A DBA can inspect it. A
backend engineer can inspect it. An AI agent can inspect it. The database
can explain its plan for it.

This shared language reduces semantic translation.

Generated glue lets teams retain that shared language without paying manual
JDBC boilerplate.

## The Compiler Becomes the First Reviewer { #compiler-first-reviewer }

If repository structure and mapping do not line up, Kora can fail during
annotation processing or KSP. If the application graph lacks a required
mapper or database component, compilation can fail.

The integration test remains necessary for actual SQL and live schema
behavior, but many Java-side mistakes never reach runtime.

This is valuable for both human and automated development.

## Kora Does Give Up Some Things { #kora-gives-up }

With Kora repositories, developers write SQL or CQL. The Java compiler
cannot fully prove arbitrary SQL against the production schema. Rich
persistence-context semantics are absent. Automatic dirty checking is
absent. Automatic relationship navigation is absent. Complex dynamic queries
may require manual code or another tool.

These are real costs.

The thesis is that many services are better off accepting them than paying
for a full ORM model they barely use.

## What Kora Gains { #what-kora-gains }

In exchange, teams get explicit queries, predictable query count, ordinary
immutable values, query-specific projections, direct database features,
generated JDBC and Cassandra boilerplate, compile-time mapping, explicit
transactions, synchronous APIs, virtual-thread-friendly concurrency, and a
much smaller semantic gap to the database.

For Kora's target workloads, that is a compelling package.

## The ORM Can Still Be the Right Tool { #orm-right-tool }

If an application genuinely revolves around persistent aggregate graphs,
automatic unit-of-work behavior, dirty tracking, relationship lifecycle, and
provider-level caching, an ORM may be the more productive model.

The right conclusion is not to remove ORM from the toolbox.

It is to stop treating ORM as mandatory infrastructure for every service
that uses a relational database.

## The Default Should Match the Common Workload { #default-common-workload }

Kora targets cloud-oriented backend services where startup, runtime
efficiency, explicit boundaries, and predictable database behavior matter.

For this workload, generated JDBC repositories are a coherent default. An
ORM can be introduced when its richer semantics are genuinely useful rather
than inherited by convention.

This is a healthy inversion of the traditional Java persistence default.

## Conclusion { #conclusion }

Kora does not need an ORM for most services because it attacks the two
historical reasons developers reached for one from a different direction.

The first problem was JDBC ergonomics. Raw JDBC requires too much repetitive
code: statements, parameter indexes, result-set loops, mapping, resource
handling, telemetry, and transaction plumbing. Kora solves that with
compile-time generated repositories and mappers. The developer writes the
database operation and the typed method; the framework writes the glue.

The second problem was blocking concurrency. Traditional synchronous JDBC
tied every waiting request to a heavyweight platform thread, which made very
high I/O concurrency expensive. Reactive database APIs offered a compelling
alternative by multiplexing work over small thread pools. Virtual threads
change that trade. A Kora service can keep a straightforward synchronous
repository call while the JVM parks the waiting virtual thread and reuses
its carrier for other work.

The resulting architecture is simple:

```text
simple synchronous repository
+
JDBC
+
virtual threads
=
high concurrency without reactive DB API
```

That simplicity does not mean the database becomes simple. The JDBC
connection pool remains finite. The database remains finite. Locks,
transactions, query plans, indexes, timeouts, and Little's Law still matter.
Virtual threads make waiting cheap; they do not make concurrency unlimited.
In fact, because the application can represent so many concurrent requests
cheaply, deliberate database concurrency limits become even more important.

Nor does the argument require declaring ORM a bad technology. ORMs solve
real problems. Persistence contexts, identity maps, dirty tracking,
cascades, relationship navigation, automatic lifecycle management, and
caching can be excellent tools for applications whose natural model is a
persistent object graph.

The provocative point is that this is not the natural model of every
service.

Many backend services are operation-oriented. They receive a request, read
several rows, apply policy, update state, write an outbox event, and return
a result. Their reads are often query-specific projections. Their writes are
often conditional updates. Their performance depends on explicit SQL,
indexes, pool capacity, and transaction design. Their domain may not benefit
from managed entity identity at all.

For these services, an ORM can introduce a second runtime model between
application code and the database: sessions, managed and detached state,
dirty snapshots, lazy proxies, flush rules, fetch plans, and caches.
Experienced teams can manage these concepts well, but they remain concepts
that every developer must learn and every incident responder may eventually
need to understand.

Kora chooses a smaller model.

SQL remains SQL. The database keeps its native language, query planner,
locking model, and vendor-specific capabilities. A PostgreSQL service can
use RETURNING, ON CONFLICT, JSONB, arrays, CTEs, or SKIP LOCKED without
waiting for another abstraction to expose them. A Cassandra service writes
CQL and respects Cassandra data modeling rather than pretending it has
relational transactions.

Java remains Java. Repository results can be immutable records or Kotlin
data classes. Query-specific projections can represent exactly the fields a
use case needs. Values do not carry hidden persistence lifecycle. Changing
an object does not silently schedule a database update. A database operation
happens because code calls a database operation.

Kora generates the glue. Parameter binding, row mapping, batch plumbing,
generated identifiers, connection use, telemetry, and repository
implementations are derived at compile time. Query macros remove repetitive
column-list maintenance without turning SQL into a framework DSL.
Transactions remain explicit. Custom mappers and manual queries provide
escape hatches when native database features require them.

Then virtual threads complete the picture. They allow Kora 2 to use this
straightforward synchronous data-access model under high I/O concurrency
without reviving the old platform-thread-per-request cost. The application's
source code can remain ordinary while the JVM handles cheap parking and
scheduling underneath.

That is why "Kora doesn't need an ORM" is not really an anti-ORM slogan. It
is a statement about abstraction economics.

If a service needs object persistence, use a tool designed for object
persistence.

If a service needs to execute well-designed database operations and map them
into typed application values, adding an object persistence model may be
unnecessary.

For a large class of modern backend services, the smaller stack is enough:

```text
explicit query
+
typed repository
+
generated glue
+
explicit transaction
+
JDBC
+
virtual threads
```

And when the smaller stack is enough, fewer hidden queries, fewer lifecycle
states, fewer caches, fewer proxies, fewer runtime layers, and fewer
concurrency abstractions are not missing features.

They are complexity the service never had to pay for.
