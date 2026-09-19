---
title: Documentation in the AI Era — Kora Framework Docs Are No Longer Just Docs
date: 2026-08-08
description: Why documentation, generated source, and compiler feedback form one explainable system in the Kora Framework for the AI era.
search:
  exclude: true
---

# Documentation in the AI Era Is No Longer Just Documentation { #ai-era-docs }
**August 8, 2026**

For most of software history, framework documentation had a simple role: a developer had a question, opened a website, searched for the relevant page, read the explanation, found an example, and
translated that information into code. When the official documentation was incomplete, the developer expanded the search outward to Stack Overflow, blog posts, conference talks, GitHub issues, source
code, or trial and error.

That model is changing.

The change is not simply that developers can now ask an AI assistant to summarize documentation. The deeper shift is that framework knowledge itself can become an interactive system. Official
reference pages, step-by-step guides, runnable examples, framework source, generated source, compiler diagnostics, test results, and agent skills can all become machine-readable context that a coding
agent uses together. Instead of merely retrieving an answer that somebody wrote before, the agent can assemble a new answer for the exact application in front of it, write the implementation, compile
it, inspect the error, correct the code, and validate the result.

The Kora Framework is unusually well positioned for this model because its architecture is already designed around explicitness. The framework generates ordinary Java and Kotlin source. Dependency wiring is
validated during compilation. Repositories, handlers, mappings, and aspects are materialized into readable code. The documentation is deliberately split between reference material, guides, and
examples. The official `kora-examples` repository contains runnable services rather than disconnected snippets. The project also maintains an official `kora-skills` repository intended to give coding
agents structured Kora-specific guidance.

Together, these pieces form something more interesting than a documentation site.

They form a **framework knowledge stack**.

The old model looked roughly like this:

```text
Developer has a question
        ↓
Documentation
        ↓
Search
        ↓
Stack Overflow
        ↓
Blog post
        ↓
GitHub issue
        ↓
trial and error
```

The emerging model looks more like this:

```text
Developer has a question
        ↓
AI agent
        ↓
Official Kora knowledge
  ├── reference documentation
  ├── guides
  ├── runnable examples
  ├── project source
  ├── generated source
  ├── framework source
  └── Kora Skill
        ↓
context-specific explanation
        ↓
project-specific code
        ↓
compiler diagnostics
        ↓
tests
        ↓
validated answer
```

That is a fundamentally different developer experience.

The central argument of this article is therefore broader than "Kora has good documentation."

> **In the AI era, framework knowledge is no longer limited to static documentation pages. Kora combines official reference documentation, guides, runnable examples, readable source code, generated
code, and an official Kora Skill into one machine-readable knowledge system that developers can query interactively through AI agents.**

The implications go beyond Kora. They change how framework documentation should be designed, how communities should think about examples, how much historical Stack Overflow volume matters, and even
what "well documented" means.

## Documentation Used to Be a Human Retrieval Problem { #human-retrieval }

Traditional documentation assumes that the developer is the retrieval engine. The framework authors publish information, and the developer must identify the right vocabulary, locate the correct page,
understand which version applies, reconcile multiple sections, translate a generic example to the application's architecture, and then test whether that interpretation was correct.

A developer asking something as concrete as "How do I build an HTTP client with retry, telemetry, authentication, and custom error mapping?" may need to understand several independent pieces:

```text
HTTP client declaration
        ↓
configuration
        ↓
interceptors
        ↓
resilience
        ↓
telemetry
        ↓
response mapping
        ↓
dependency injection
```

Even if every piece is documented correctly, the developer still has to compose them. That composition work has historically been one of the largest hidden costs of framework adoption. Documentation
rarely fails only because a page is missing. It also fails because the information is fragmented across multiple pages and the developer must construct the solution mentally.

This is why large framework communities became so valuable. Somebody, somewhere, had usually already performed the composition.

## The Historical Power of Stack Overflow { #stack-overflow }

For more than a decade, one of the strongest advantages of a mature framework was not merely its official documentation. It was the accumulated archive of questions and answers around it.

The practical workflow was often:

```text
error message
    ↓
Google
    ↓
Stack Overflow result
    ↓
copy/adapt solution
```

The community corpus acted as an enormous cache of previously solved combinations. Official documentation might explain transaction management and async execution separately, while Stack Overflow
might contain the exact question: "Why is my transaction not active inside this async method?"

That specificity was extraordinarily valuable because a human developer did not need to derive the interaction from first principles. A mature framework accumulated tens of thousands of these
interaction-level answers over time, and a younger framework naturally looked weaker by comparison.

## AI Changes the Economics of Missing Historical Answers { #missing-answers-economics }

AI agents weaken this historical advantage, although they do not eliminate it.

An agent does not necessarily need somebody to have asked the exact question before. If the authoritative sources describe the relevant pieces accurately, the agent can combine them.

```text
Docs say A
Guide explains B
Example demonstrates C
Generated source reveals D
Compiler reports E
        ↓
agent composes A + B + C + D + E
        ↓
solution for this application
```

This is a different form of knowledge reuse. Instead of retrieving one historical answer that happens to match the situation, the agent synthesizes a new answer from canonical building blocks.

That leads to a powerful new principle:

> **A framework no longer needs a historical answer for every possible question if its authoritative sources are complete enough for an agent to derive the answer.**

This does not make community knowledge irrelevant. Real production incidents, undocumented edge cases, regressions, and strange integrations still benefit enormously from human reports. But it changes
the minimum viable knowledge ecosystem for a framework.

A smaller framework can compensate for a smaller historical community corpus if its authoritative knowledge is structured enough to support reliable derivation.

## The Metric Changes From Archive Size to Derivability { #derivability-metric }

The old question was:

```text
How many answers about this framework exist?
```

The new question is increasingly:

```text
Can an agent derive the correct answer
from authoritative sources?
```

Those are not the same metric.

A framework may have a vast archive but poor derivability because multiple generations of APIs coexist, old answers dominate search results, deprecated approaches remain popular, documentation
contradicts old blog posts, several programming models solve the same problem differently, examples use stale conventions, or runtime behavior depends on hidden rules.

Another framework may have a much smaller archive but excellent derivability because there is one recommended path, reference pages are dense and current, guides explain workflows, examples are
runnable, generated code exposes implementation details, compiler diagnostics constrain mistakes, and source code is easy to inspect.

Kora is deliberately moving toward the second model.

## Kora Already Frames Documentation as More Than Pages { #kora-frames-docs }

The Kora 2 landing page does something notable: it does not describe documentation only as a website.

It presents documentation, guides, runnable examples, generated sources, compiler feedback, and AI-assisted development as parts of one learning and development system. It also explicitly claims that
more than 95% of framework functionality is covered through documentation, guides, and examples, and separates that coverage into substantial sets of step-by-step guides and module references.

Whether one agrees with every percentage as a universal measurement methodology is less important than the underlying structure. The framework is trying to maintain several layers of canonical
knowledge rather than one monolithic manual.

That structure is exactly what AI agents benefit from.

## A Framework Knowledge Stack { #knowledge-stack }

The most useful way to think about Kora's knowledge model is as a stack:

```text
Reference documentation
        ↓
Guides
        ↓
Runnable examples
        ↓
Application source
        ↓
Generated source
        ↓
Framework source
```

An AI access layer can sit across all of them:

```text
Docs ───────────┐
Guides ─────────┤
Examples ───────┤
Application ────┤
Generated code ─┤
Framework code ─┤
                ↓
          Kora Skill
                ↓
            AI agent
                ↓
     context-specific answer
                ↓
        compiler + tests
```

The key insight is that these layers do not duplicate one another. Each one carries a different kind of truth.

## Reference Documentation Provides Facts { #reference-facts }

Reference documentation should answer precise questions: which annotation declares a component, what configuration keys an HTTP server accepts, which repository return types are supported, how
`ValueOf<T>` behaves, what the default timeout is, which telemetry components can be overridden, which tags select a component, and which dependencies are required for a module.

These answers should be dense and predictable. Reference material is not the ideal place for a long conceptual essay explaining why an architecture was chosen. Its job is to be authoritative about
interfaces and behavior.

This becomes even more important for AI retrieval. Agents often need exact facts. A concise reference section saying "property X, type Duration, default 30s" is more useful for retrieval than several
paragraphs of narrative surrounding the same fact.

## Guides Provide Reasoning and Workflow { #guides-reasoning }

Guides solve a different problem. A guide answers: "How do I accomplish a complete task correctly?"

For example:

```text
create application
        ↓
configure HTTP
        ↓
add controller
        ↓
add database
        ↓
add repository
        ↓
add telemetry
        ↓
test
```

A good guide has narrative because sequence matters. It can explain why a dependency exists, why a particular pattern is recommended, and how several APIs fit together.

That is the correct place for reasoning. Separating reference from guides therefore improves both human reading and AI retrieval. The reference gives facts. The guide gives process.

## Examples Provide Canonical Implementations { #examples-canonical }

Examples are a third category. They answer: "What does a correct implementation actually look like?"

This is different from both reference and explanation.

The `kora-examples` repository is particularly valuable because it is designed as a runnable playground. Examples are self-contained services, available in Java and Kotlin, with real configuration and
tests. The repository explicitly invites developers to run them, break them, inspect them, and use them alongside the guides.

That makes examples executable evidence. An agent does not have to infer the final file structure from documentation prose. It can inspect a complete working module.

This gives the knowledge stack a practical anchor.

## Examples Become Much More Valuable With Agents { #examples-with-agents }

Historically, an example had to be reasonably close to the developer's exact use case to be useful. Suppose the example showed a simple JDBC repository, but the application needed JDBC plus
transaction handling, custom mapping, and telemetry. The developer had to adapt the pattern manually.

An agent changes that:

```text
agent reads canonical example
        ↓
extracts the structural pattern
        ↓
reads relevant reference sections
        ↓
adapts pattern to project
        ↓
compiles
        ↓
corrects differences
```

This leads to an important shift:

> **Examples no longer have to match the developer's exact use case. An agent can use them as canonical building blocks and specialize them automatically.**

That makes a relatively small set of high-quality examples far more powerful than a very large pile of narrowly targeted snippets.

## Runnable Examples Are Better Than Isolated Snippets { #runnable-examples }

This matters because AI agents are extremely good at copying patterns, including bad ones.

A documentation snippet may omit dependencies, imports, application composition, configuration, testing, lifecycle, or error handling. A runnable example cannot omit all of those and still run.

That makes runnable examples a stronger canonical source. The agent can see not only a repository interface, but the `build.gradle`, application config, DI graph, service, controller, and test.

The example demonstrates the integration boundary end to end. For machine-assisted development, that is significantly more valuable.

## Code Itself Becomes Part of the Documentation System { #code-as-docs }

Kora has another property that becomes much more important in the AI era: the framework is intentionally inspectable.

Generated infrastructure becomes ordinary Java or Kotlin source. That means documentation is not the final layer of explanation.

If a developer asks how exactly a controller is invoked, the agent can inspect the generated HTTP handler. If the question is what a repository interface became, the agent can inspect the generated
repository implementation. If the question is which components are created in what order, the generated application graph can reveal the wiring. If the question is how an AOP annotation wrapped the
method, the generated subclass or wrapper can show the actual execution path.

This creates a hierarchy of evidence.

## Readable Source Is Documentation Too { #readable-source }

For an AI agent, readable source code is documentation.

That statement sounds obvious, but many framework architectures make it surprisingly hard to exploit. If the effective behavior lives in runtime proxy state, reflection metadata, dynamically generated
bytecode, container registries, or framework internals assembled only during startup, then reading source does not necessarily reveal the behavior directly. An agent has to infer the runtime
transformation.

Kora reduces that gap. The generated code is deliberately intended to look like code an engineer could write by hand. Therefore the agent can reason from implementation rather than guess from
abstraction.

This turns generated source into something close to **executable documentation**.

## Executable Documentation Is Stronger Than Narrative Alone { #executable-docs }

Written documentation says:

```text
Kora will generate a repository implementation.
```

Generated code shows:

```text
this is the repository implementation Kora generated
for this exact application
with these exact mappings
```

Written documentation says the graph resolves a dependency. Generated code shows which factory creates which component and which dependency is passed. Written documentation says an aspect surrounds a
method. Generated code shows the call order.

This is context-specific truth. The difference is enormous for debugging.

## The Agent Can Move Down the Stack Until Uncertainty Disappears { #agent-down-stack }

Imagine a developer asks: "Why does my retry happen outside the transaction?"

An agent can begin with the documentation. If the docs explain aspect ordering clearly, the answer may be obvious. If not, the agent can inspect the generated AOP wrapper. If that is still
insufficient, it can inspect the framework aspect implementation. Then it can compile a minimal test.

The knowledge process becomes:

```text
reference
   ↓
generated implementation
   ↓
framework implementation
   ↓
compiler/test
```

At each step, uncertainty decreases. That is far more powerful than searching for a blog post describing a similar case from three years ago.

## Compiler Diagnostics Are Part of the Knowledge System { #compiler-diagnostics }

Because so much Kora framework structure is validated at compile time, the compiler is not merely a build tool. It is an interactive source of framework knowledge.

Suppose an agent writes an invalid graph. The compiler can report a missing dependency, ambiguous component, invalid cycle, unsupported contract, mapper generation failure, or repository generation
failure.

The agent then uses that diagnostic to refine its understanding:

```text
agent hypothesis
      ↓
code
      ↓
compiler
      ↓
structured disagreement
      ↓
agent correction
```

This is a remarkably effective learning interface.

## Compiler Errors Are Better Than Silent Guessing { #compiler-errors }

AI coding has one persistent weakness: plausible code is not necessarily correct code.

A model can invent annotations that look reasonable, configuration keys that resemble another framework, APIs from an older version, or unsupported combinations. Strong compile-time validation
constrains that hallucination space.

Instead of relying on the agent's confidence, the toolchain answers. Kora's design therefore turns the compiler into a second knowledge authority after the documentation.

The docs say what should work. The compiler tells the agent whether this exact implementation does.

## Tests Close the Loop { #tests-close-loop }

Compiler correctness is not behavioral correctness. The final layer is testing.

A Kora agent workflow can therefore be:

```text
retrieve
   ↓
generate
   ↓
compile
   ↓
fix structural errors
   ↓
start context
   ↓
run component/integration tests
   ↓
fix behavioral errors
```

This gives the knowledge system a verification cycle. The agent is not only reading. It is testing its interpretation.

That is what makes documentation increasingly executable.

## The Official Kora Skill Changes the Interface { #kora-skill-interface }

The official `kora-skills` repository is one of the most interesting parts of this architecture because it formalizes how an agent should approach Kora.

A static documentation site is passive. The developer must navigate it. A skill provides an instruction layer for the agent.

It can encode where canonical sources are, which patterns are preferred, which areas of the framework have dedicated guidance, how to interpret Kora concepts, which commands or examples should be
consulted, and how to avoid outdated or incompatible approaches.

This changes the interface from:

```text
developer → documentation
```

to:

```text
developer → agent → framework knowledge
```

The agent becomes an active retrieval and adaptation layer.

## The Skill Is More Than a Search Shortcut { #skill-search-shortcut }

The weakest interpretation of an AI skill would be a file containing links. That would not be very interesting.

The stronger model is:

```text
canonical framework instructions
+
domain-specific decomposition
+
versioned conventions
+
links to authoritative sources
+
agent workflow
```

The current official Kora Skills repository is structured into many domain-specific skills covering areas such as DI, configuration, HTTP, data access, messaging, gRPC, telemetry, AOP, testing,
project setup, and learning.

That is essentially a machine-oriented map of framework knowledge. It tells the agent not merely where information is but how to reason about the framework.

## Versioned Skills Matter { #versioned-skills }

There is an important current-state detail.

The official skills repository presently publishes a package named `kora-v1`, targeting the Kora 1.x line. The repository deliberately uses that name so that a future `kora-v2` package can carry
separate guidance where Kora 2 requires it.

At the same time, the Kora 2 landing page already links the official skills repository and presents AI-assisted learning as part of the framework experience.

That should not be blurred into the claim that today's `kora-v1` package is already a complete Kora 2 knowledge package.

The more interesting conclusion is architectural:

**Kora is treating agent knowledge as a versioned framework interface.**

That is exactly the right direction. A skill that ignores framework generations would recreate one of the biggest problems of historical web search: mixing incompatible eras.

Versioned agent knowledge can avoid that.

## Versioning Is Critical for AI Reliability { #versioning-ai-reliability }

AI retrieval becomes dangerous when several framework generations use similar vocabulary.

Suppose Kora 1 and Kora 2 share concepts but differ in contracts, package names, execution model, or supported features. A generic model may mix them. That is the same problem developers have
experienced for years with old Stack Overflow answers.

A versioned skill can tell the agent:

```text
You are working on Kora 2.
Do not use Kora 1 guidance unless explicitly relevant.
```

This makes the skill more than convenience. It becomes a **version boundary for machine reasoning**.

## Static Documentation Becomes Interactive Documentation { #interactive-docs }

Imagine the developer asks:

> Add a Kora HTTP client with retry, telemetry, and custom error mapping to this service.

Without an agent, the developer may need to inspect HTTP client reference, resilience reference, telemetry reference, mapping reference, configuration reference, and examples.

With an agent and canonical Kora context, the process can become:

```text
question
  ↓
agent identifies subproblems
  ↓
retrieves HTTP client rules
  ↓
retrieves resilience rules
  ↓
retrieves telemetry conventions
  ↓
reads current application graph
  ↓
reads closest runnable example
  ↓
writes project-specific implementation
  ↓
compiler validates
  ↓
tests validate
```

The documentation has become interactive. Not because the HTML page changed, but because the access model changed.

## The Documentation Becomes Executable Context { #executable-context }

This leads to one of the strongest formulations:

> **The documentation does not merely tell developers how Kora works anymore. It can become executable context for the agent that is helping them write the application.**

The phrase *executable context* does not mean the prose itself runs. It means the knowledge can directly drive code generation and then be tested against the compiler.

The distance between reading documentation and producing validated implementation shrinks dramatically.

That changes how framework authors should think about documentation quality.

## Documentation for Humans and Agents Has Different Failure Modes { #failure-modes }

Human readers tolerate some ambiguity because they bring broad judgment. An AI agent can amplify ambiguity.

If two pages show two legitimate but different patterns, the agent may combine them incorrectly. If old and new APIs coexist without clear versioning, the agent may generate a hybrid. If a reference
page contains a deprecated example but does not mark it strongly, the agent may treat it as current. If documentation repeats the same concept with slightly different terminology, retrieval can become
less precise.

Therefore machine-readable documentation places new pressure on documentation design.

## Dense Documentation Becomes More Valuable { #dense-docs }

"More documentation" is not always better.

A very large corpus may contain repetition, historical artifacts, contradictory patterns, obsolete APIs, abandoned integrations, multiple generations, and duplicated explanations. Humans already find
such corpora difficult. Agents also suffer because retrieval quality depends on signal density.

A smaller, denser corpus with clear structure can outperform a huge archive. This is particularly relevant to Kora because the project explicitly prefers a small conceptual surface and one recommended
path for common problems.

The framework's philosophy and its documentation strategy reinforce one another.

## One Recommended Path Reduces Retrieval Ambiguity { #recommended-path }

Consider an agent asked: "How should I create a database repository?"

If the framework ecosystem contains many generations, reactive and blocking variants, legacy DAO layers, ORMs, templates, functional DSLs, and several annotation models, the agent must first decide
which worldview applies.

That decision may depend on framework version, team convention, performance requirement, and historical context.

Kora intentionally narrows the choice space. For Kora 2, the current direction is much clearer:

```text
repository contract
+
explicit query
+
generated implementation
+
synchronous virtual-thread execution
```

A smaller option space improves agent reliability.

## Documentation Quality Becomes More Important Than Documentation Size { #quality-over-size }

Traditional framework comparisons often ask how many pages, tutorials, Stack Overflow questions, or blog posts exist.

In the AI era, better questions are:

```text
Is the information authoritative?
Is it current?
Is it versioned?
Is it structured?
Is terminology consistent?
Are examples executable?
Can behavior be inspected in source?
Can the compiler validate the result?
```

The volume of text is secondary.

This is why "95% documented" is more meaningful when the coverage is distributed across the right knowledge layers rather than concentrated in one gigantic manual.

## A Monolithic Documentation Site Is Not Necessarily Better { #monolithic-site }

A documentation site can become too ambitious. It may attempt to be simultaneously reference, tutorial, cookbook, conceptual guide, migration guide, FAQ, troubleshooting wiki, and historical archive.

That creates noise. The same concept appears repeatedly in different voices. Search results become harder to rank. Agents retrieve chunks without always understanding the document's role.

A layered documentation architecture is healthier.

## The New Division of Responsibilities { #division-responsibilities }

A strong framework knowledge system can use this division:

```text
Reference
→ precise facts

Guides
→ reasoning and workflows

Examples
→ canonical implementations

Generated source
→ exact application-specific behavior

Framework source
→ ultimate implementation truth

Skill
→ retrieval and adaptation strategy

Compiler
→ structural validation

Tests
→ behavioral validation
```

Every layer has a job. This reduces duplication and gives an AI agent a rational escalation path when the first source is insufficient.

## Reference Should Not Become a Tutorial { #reference-not-tutorial }

Suppose the developer wants to know the exact type of a configuration property. The answer should be retrievable quickly.

If the relevant page contains several pages of conceptual introduction before the property table, retrieval becomes harder.

This is why concise reference material is valuable. The tutorial can explain when to use the property. The reference should state exactly what it is.

That separation helps both humans and agents.

## Guides Should Not Become API Catalogs { #guides-not-catalogs }

The opposite problem is equally common. A guide becomes unreadable when every possible configuration option is inserted into the workflow.

The guide should show the common path and explain the reasoning. The reference owns exhaustive details.

This keeps the guide useful for context construction. An agent can combine the guide's sequence with the reference's exact values.

## Examples Should Be Canonical, Not Exhaustive { #examples-canonical-not-exhaustive }

An examples repository does not need one service for every permutation. It needs examples that demonstrate canonical patterns cleanly.

An agent can specialize them. That changes how maintainers should allocate effort.

Instead of writing many nearly identical examples for every combination, it can be more valuable to maintain a smaller number of high-quality examples that compose major patterns correctly.

The agent handles the permutation.

## Generated Source Is Application-Specific Documentation { #generated-source-docs }

Static examples can never exactly match the current project. Generated source can.

Suppose a developer has a repository interface. The documentation can explain how repositories work. The example can show another repository. But the generated implementation for this repository shows
the exact code Kora produced for the application's contract.

For debugging and explanation, that source has unusually high value.

## Generated Graph Code Is Architectural Documentation { #generated-graph-code }

The same applies to dependency injection. An architecture diagram might say:

```text
Controller → Service → Repository
```

The generated graph shows the actual instantiation path.

An agent can inspect which factory created the component, which tag selected an implementation, which dependencies are direct, where `ValueOf<T>` appears, and how lifecycle components are composed.

That makes architecture queryable.

A developer can ask: "Why is this component in the graph?" and the agent can answer from code rather than framework mythology.

## Generated AOP Code Documents Control Flow { #generated-aop-code }

AOP is usually one of the least transparent parts of enterprise frameworks.

An annotation may look simple, but actual execution order can be difficult to reconstruct when proxies and interceptors compose dynamically.

Generated AOP changes the knowledge problem. The agent can inspect the wrapper or subclass and answer whether retry is outside transaction, transaction outside cache, or logging around all of them
based on the actual generated call structure.

This is executable documentation in a very literal sense.

## Framework Source Is the Final Authority { #framework-source-authority }

Sometimes documentation and generated code are still not enough. Then open-source framework code becomes the final layer.

An agent can trace annotation processors, runtime interfaces, module implementations, telemetry factories, and lifecycle code.

This is not unique to Kora; open-source frameworks have always allowed source inspection. What is different is that AI makes source inspection dramatically cheaper.

A human developer may hesitate to read hundreds of lines of processor code. An agent can summarize it, find the relevant branch, and explain how it relates to the current application.

Open source therefore becomes more valuable as documentation than it used to be.

## Source Transparency Is an AI Multiplier { #source-transparency }

Framework source that is strongly typed, direct, small, consistent, and close to generated output is easier for agents to reason about.

Kora's emphasis on transparent generated code and simple abstractions has an unexpected consequence: it creates a high-quality machine-readable implementation corpus.

The same code quality that helps maintainers also helps models.

## Error Messages Become Teaching Material { #error-messages-teaching }

Imagine a new developer asks an agent to add a component and compilation fails because the graph contains an ambiguity.

The agent reads the error. That error teaches that there are two valid candidates, the dependency is not tagged, and the graph requires disambiguation.

The agent can then explain the concept while fixing it. This transforms framework diagnostics into interactive teaching material.

In older workflows, the developer might copy the error into Google. Now the compiler and agent can form a closed loop.

## Learning Becomes Embedded in Work { #embedded-learning }

Traditional learning often happens before development:

```text
read tutorial
watch talk
build sample
then work on real service
```

AI-assisted learning can happen inside development:

```text
ask question
agent explains concept
agent changes project
compiler responds
developer sees result
```

This is closer to apprenticeship than documentation search. The framework knowledge is delivered at the moment it is needed.

Kora's explicit model suits that style particularly well.

## The Skill Becomes an Interactive Access Layer { #skill-access-layer }

This is the most important role of the official Kora Skill.

The Skill should not replace the documentation. It should sit on top of it.

```text
Docs
Guides
Examples
Source
        ↓
Kora Skill
        ↓
AI agent
        ↓
developer
```

The Skill can encode the correct retrieval strategy and conventions.

In other words, it becomes an **interactive access layer over canonical framework knowledge**.

That is a new category of developer tooling.

## A Skill Is Closer to an API for Knowledge { #skill-api-knowledge }

Documentation is optimized for reading. A skill is optimized for an agent consuming knowledge while performing work.

That difference is similar to the difference between a web page and an API. The underlying information may overlap, but the interface is different.

A well-designed skill can say: consult this guide for project setup, use this repository example for JDBC, avoid legacy patterns, inspect generated source for graph questions, run compilation after
wiring changes, and prefer the current recommended module.

This turns framework conventions into machine-consumable operational instructions.

## Machine-Readable Does Not Mean Machine-Only { #machine-readable }

The best machine-readable knowledge remains good human documentation.

Clear headings, consistent terminology, explicit contracts, concise examples, and strong version boundaries help both.

The AI era does not justify writing documentation as opaque metadata for models. It increases the value of clarity.

The same structure improves human scanning, search engines, embeddings, RAG retrieval, and agent reasoning.

Good documentation design is increasingly multi-audience by default.

## The Kora Knowledge Stack Is Not Just the Skill { #stack-not-just-skill }

It would be a mistake to reduce the idea to "Kora has an AI skill."

The skill is useful because the underlying framework knowledge is already structured. Without good sources, a skill only gives an agent faster access to bad information.

The real stack is:

```text
authoritative reference
+
reasoned guides
+
runnable examples
+
inspectable code
+
versioned skill
+
compiler feedback
+
tests
```

The components reinforce one another.

## Why 95% Coverage Matters Differently Now { #coverage-matters }

Coverage percentages have always been difficult to compare because frameworks define "functionality" differently.

Nevertheless, the idea of broad official coverage becomes more important with AI because missing canonical information forces the model to improvise.

An undocumented edge may cause the agent to rely on stale training data, old GitHub issues, community guesses, or analogies to another framework.

Every well-documented area reduces that uncertainty.

High official coverage therefore has a second-order effect: it improves the reliability of automated development.

## Documentation Gaps Become Hallucination Gaps { #hallucination-gaps }

This is a useful way to think about it.

If an API is undocumented, a human developer knows they are uncertain. An AI model may still produce a plausible answer.

That is more dangerous.

Therefore framework documentation in the AI era is partly about **constraining hallucination**.

Strong documentation says:

```text
this is the supported API
this is the configuration
this is the recommended path
```

Compiler validation adds another constraint.

Together they reduce the space in which an agent can confidently invent something.

## One Recommended Path Is an Anti-Hallucination Feature { #anti-hallucination }

Kora's "one problem, one solution" philosophy has a new consequence in this environment.

For humans, fewer choices reduce cognitive load. For agents, fewer valid solution families reduce ambiguity.

Suppose there are ten ways to create an HTTP client. A model can choose a technically valid but organizationally wrong one. If the framework strongly recommends one approach, the agent has a narrower
search space.

That improves consistency.

## Legacy Compatibility Can Be an AI Liability { #legacy-ai-liability }

Large mature frameworks often carry old APIs for good reasons. Breaking millions of applications is unacceptable.

But every legacy layer increases the amount of context an AI agent must distinguish. A search result may show a 2017 solution, a 2020 solution, a 2023 solution, and a 2026 solution. All may have been
correct at some point.

A human expert recognizes the era. A model may blend them.

Versioned documentation and skills can reduce this problem.

A younger framework like Kora has less historical baggage, which becomes an unexpected advantage for machine reasoning.

## "Docs Without the Bloat" Becomes Technically Meaningful { #docs-without-bloat }

The phrase can sound like marketing, but there is a serious technical point behind it.

Retrieval systems work better when relevant passages are dense, terminology is stable, duplicated text is limited, obsolete variants are clearly separated, and page boundaries correspond to concepts.

A large watery documentation corpus may actually be worse for an AI agent than a smaller high-signal one.

This is the machine-readable version of the same complaint humans have about bloated documentation.

## Repetition Is Not Free { #repetition-not-free }

Documentation authors sometimes repeat the same explanation across many pages to make each page self-contained. That can help casual human browsing, but it can also create inconsistencies.

One page is updated. Another is not. An agent retrieves both. Now canonical knowledge conflicts with itself.

A layered knowledge system should centralize facts and let guides link to reference rather than duplicating every detail.

This makes maintenance and machine retrieval more reliable.

## The Same Principle Applies to Examples { #principle-examples }

Duplicated examples can drift. Suppose five examples contain slightly different ways to configure the same module. An agent may not know which one is canonical.

A smaller set of carefully maintained examples is often better.

Again, quality beats volume.

## Community Knowledge Still Matters, But Its Role Changes { #community-knowledge }

None of this makes Stack Overflow, blogs, conference talks, or GitHub issues obsolete.

They remain valuable for undocumented bugs, production lessons, edge cases, migration experiences, performance discoveries, alternative architectures, and historical context.

But they should increasingly sit outside the canonical core.

The agent should prefer official current source, then use community material as secondary evidence when the canonical sources are insufficient.

This is a healthier hierarchy than treating the most upvoted 2019 answer as authoritative forever.

## Canonical Sources Become More Valuable Than Popular Sources { #canonical-sources }

Search engines historically optimized heavily for popularity. AI development needs authority.

A highly linked blog post may be obsolete. A small official guide may be current.

The agent should know the difference.

An official Skill can help encode that priority.

That is another reason skills are more interesting than generic web search.

## The Framework Can Teach the Agent Its Own Conventions { #teach-conventions }

This is perhaps the most novel possibility.

A framework's Skill can say, in effect:

```text
When solving problem X,
prefer approach Y.

When working with Kora 2,
do not use deprecated Kora 1 pattern Z.

When debugging DI,
inspect generated graph code.

When building an HTTP client,
start from OpenAPI where appropriate.

After modifying graph contracts,
compile before continuing.
```

That is not documentation in the old sense.

It is a machine-readable development methodology.

## Framework Conventions Become Programmable Context { #programmable-context }

Every experienced team has unwritten framework conventions.

For example:

```text
always use this module
never use that lower-level API
prefer OpenAPI first
use ValueOf only when refresh semantics require it
```

Historically these lived in senior engineers' heads, onboarding presentations, internal wiki pages, and code review comments.

A skill can encode them directly for the agent. This reduces repeated review work.

Kora's official skill model points in this direction.

## Official Skills Can Reduce Model Drift { #reduce-model-drift }

Generic language models have stale knowledge. Frameworks evolve faster than model training cycles.

A maintained official skill gives the agent a current overlay.

This is especially important for smaller frameworks where a model's pretrained Kora knowledge may be limited or biased toward older releases.

The framework team can effectively publish updated context without waiting for a new foundation model.

That is a major change in framework documentation economics.

## Documentation Releases Can Become Agent Releases { #agent-releases }

Historically, a framework release involved:

```text
code
+
docs
+
release notes
```

The emerging model may be:

```text
code
+
docs
+
examples
+
migration guide
+
agent skill
```

The skill becomes another compatibility artifact.

If framework behavior changes materially, machine guidance should change with it.

That is why versioned skills are so important.

## Kora 1 and Kora 2 Illustrate the Need for Version Boundaries { #version-boundaries }

Kora is currently in exactly the situation where this matters.

Kora 2 changes important assumptions relative to the 1.x line. An agent skill that silently mixes those eras would be dangerous.

The `kora-v1` naming in the official repository is therefore a good architectural decision: it treats AI guidance as version-specific knowledge rather than universal prose.

A future Kora 2 skill should be able to describe Kora 2 directly without carrying accidental 1.x assumptions.

This is what responsible machine-readable documentation should look like.

## The Skill Can Become the Framework's Query Planner { #skill-query-planner }

A useful analogy is a database query planner.

The developer supplies intent:

```text
I need an HTTP client with auth and retries.
```

The skill can help the agent decompose that into relevant framework knowledge:

```text
HTTP client
authentication
resilience
telemetry
configuration
testing
```

Then the agent queries the appropriate sources.

The developer does not need to know the exact documentation taxonomy.

That reduces navigation cost.

## Developers Stop Needing the Exact Search Term { #no-search-term }

This is an important usability improvement.

Traditional docs often require vocabulary knowledge before they are useful. A beginner may search for "how do I keep service alive after config changes" while the framework calls the mechanism
`ValueOf` or `RefreshableGraph`.

A search engine may or may not bridge the vocabulary. An agent can.

It can interpret intent, map it to framework terminology, and retrieve the correct material.

This makes documentation accessible earlier in the learning curve.

## AI Makes Good Taxonomy More Valuable, Not Less { #good-taxonomy }

Although the agent can bridge vocabulary, a consistent framework taxonomy still matters.

The skill and documentation need stable concepts to map intent onto.

Kora's relatively small set of primitives helps. Concepts such as `Component`, `Module`, `Repository`, `Controller`, `ValueOf`, and `Telemetry` form a manageable ontology.

That makes retrieval and explanation easier.

## The Framework Knowledge Stack Can Be Queried From the Project Context { #queried-project-context }

The most significant advantage over ordinary documentation search is that the agent sees the current project.

The answer can therefore depend on Java or Kotlin, existing modules, Gradle dependencies, current config structure, tags already in use, generated sources, test setup, and framework version.

Instead of answering "Here is how Kora HTTP clients generally work," the agent can answer: "In this project, you already use the OkHttp transport, the telemetry module is present, and your error DTO
mapper exists. Add this client interface, reuse this mapper, and attach retry here."

That is context-specific documentation.

## Context-Specific Documentation Is More Useful Than Generic Documentation { #context-specific-docs }

This is the central experiential shift.

Static documentation describes the framework.

An agent describes **the framework as instantiated in your codebase**.

That can include which module is already present, which generated class exists, which implementation wins DI, which configuration path is currently used, and which test style the repository follows.

This narrows the gap between learning and modifying the system.

## Generated Sources Make Project Context Much Richer { #generated-project-context }

Kora's generated source adds information that many frameworks hide.

An agent can inspect not only handwritten declarations but also the framework's interpretation of them.

This means the project context contains both intent and materialized implementation.

That duality is extremely valuable.

The model can compare what the developer wrote with what Kora generated.

## Compiler Diagnostics Add a Third View { #compiler-third-view }

Now the agent has three perspectives:

```text
handwritten declaration
generated implementation
compiler feedback
```

That triangulation makes framework reasoning much more robust.

If the docs are misunderstood, the compiler corrects the interpretation. If the generated code surprises the developer, the agent can explain why.

This is a richer knowledge environment than static docs alone.

## Tests Add the Fourth View { #tests-fourth-view }

Then tests add behavioral evidence.

The full loop becomes:

```text
Docs: what should happen
Source: what developer asked for
Generated code: what framework produced
Compiler: whether structure is valid
Tests: whether behavior is correct
```

An agent can move across all five.

That is close to a complete interactive knowledge system.

## The Framework Knowledge Stack Has Feedback, Not Just Retrieval { #feedback-not-retrieval }

This is the distinction between an information system and a development system.

A documentation site returns text.

The Kora knowledge stack can produce:

```text
answer
→ implementation
→ compiler result
→ test result
→ revised answer
```

The output feeds back into the next reasoning step.

That closed loop is why AI-assisted development feels qualitatively different from search.

## The Compiler Is an Oracle With Limited Scope { #compiler-oracle }

Of course, the compiler does not know business correctness.

It cannot tell whether a retry is semantically safe, whether a SQL query has the right index, whether a metric will explode cardinality in production, or whether a timeout policy is operationally
sensible.

The knowledge stack therefore still depends on human engineering judgment.

But the compiler is extremely good at rejecting structural nonsense.

That is exactly where AI agents benefit from hard constraints.

## Tests Are an Oracle With Another Scope { #tests-oracle }

Tests also have limits. They validate only covered behavior.

An agent can write a passing test for the wrong requirement.

Therefore the final system is not:

```text
AI + docs = guaranteed correctness
```

It is:

```text
AI + canonical context + compiler + tests
= much shorter path to a plausible, validated implementation
```

Human review remains essential.

The point is that documentation participates directly in that loop.

## This Changes What Framework Authors Should Optimize { #what-to-optimize }

Historically, documentation teams optimized for page views, readability, and discoverability.

Now they should also optimize for chunk quality, stable terminology, version boundaries, canonical examples, source traceability, unambiguous configuration tables, machine-consumable conventions, and
agent instructions.

This is a new documentation discipline.

## Documentation Should Be Treated Like Code { #docs-like-code }

If AI agents depend on documentation operationally, docs become part of the development toolchain.

That implies software-like quality practices: review, versioning, tests where possible, examples compiled in CI, stale-link checks, API consistency checks, and synchronized migration docs.

A broken example is no longer just an educational inconvenience.

It can become bad input to automated coding.

## Runnable Examples Should Be Continuously Verified { #examples-continuously-verified }

The best examples repository should be part of CI.

If a framework release changes an API, examples should fail immediately.

This prevents the knowledge stack from drifting.

Kora's runnable examples are well suited to this approach because they are actual applications rather than prose snippets.

That is exactly the kind of artifact agents can trust more confidently.

## Generated-Code Stability Also Matters { #generated-code-stability }

Generated source does not need to be a public API in the strict compatibility sense to be useful as documentation.

But it should remain readable and semantically stable enough that humans and tools can inspect it.

If generation becomes intentionally opaque or aggressively obfuscated, one of Kora's strongest AI-era advantages disappears.

Readability is therefore not merely a debugging nicety. It is part of the knowledge architecture.

## Error Message Quality Becomes an AI Feature { #error-message-quality }

Compiler diagnostics traditionally target humans. Now they also target agents.

An error such as "cannot resolve dependency" is less useful than one that explains which component requires which dependency, what candidates exist, and how to remove the ambiguity.

The more structured the diagnostic, the faster an agent can self-correct.

Kora's compile-time model creates the opportunity for this kind of feedback.

## AI Changes the Value of Framework Transparency { #framework-transparency }

Transparency has always been useful. In the AI era it becomes multiplicative.

A human may decide not to inspect framework internals because the effort is too high. An agent can inspect them cheaply.

Therefore every transparent layer becomes usable more often.

Generated code that only a small percentage of human developers would inspect may be inspected automatically by an agent whenever something is unclear.

That increases the return on transparency.

## Hidden Runtime Magic Becomes More Expensive { #hidden-runtime-magic }

The opposite is also true.

Hidden runtime behavior creates uncertainty that agents must reconstruct. A model may need to infer proxy boundaries, bean post-processing, container conditions, reflection registration, runtime
classpath discovery, or implicit ordering.

If the information is not visible in source, the agent must rely more heavily on documentation or simulation.

This increases hallucination risk.

Kora's explicit architecture reduces that hidden state.

## Documentation and Framework Architecture Are Converging { #converging-architecture }

This is one of the most interesting consequences.

Documentation quality is no longer independent of framework architecture.

A transparent framework is inherently easier to document because the implementation is inspectable. A heavily dynamic framework can still have excellent documentation, but the documentation must
explain more invisible machinery.

Kora's generated-code model means that part of the explanation can live in the generated artifact itself.

Architecture therefore affects knowledge quality.

## Kora's Small Surface Area Is an AI Advantage { #small-surface-area }

A smaller conceptual surface means fewer framework-specific tokens need to be loaded into context.

An agent can spend more of its context window on the application, domain code, tests, architecture, and actual problem.

This matters in large codebases.

Framework complexity consumes attention, whether human or machine.

Kora's explicit effort to keep abstractions small has a new benefit: lower context overhead.

## Context Windows Are a Real Engineering Resource { #context-windows }

An LLM has finite context.

If understanding the framework requires loading dozens of abstractions, legacy APIs, proxy rules, configuration conventions, and multiple execution models, less context remains for the application
itself.

A framework with a compact model is cheaper to reason about.

This is a very literal sense in which simplicity becomes performance for AI development.

## Dense Documentation Saves Context Tokens { #dense-saves-tokens }

A concise reference page with high information density consumes fewer tokens than a long repetitive explanation.

That gives dense documentation another machine-era advantage.

It can fit more relevant framework knowledge into the same reasoning context.

This does not mean documentation should be cryptic. It means unnecessary repetition has a measurable cost.

## Guides Supply the Context That Reference Cannot { #guides-supply-context }

Token efficiency does not imply removing reasoning.

The solution is separation. Reference stays dense. Guides carry conceptual explanations when needed. The agent loads the guide only for tasks that require reasoning.

That is a better use of context than making every page self-contained and verbose.

## Skills Can Load Knowledge Selectively { #skills-load-selectively }

A well-structured skill repository can further reduce context cost.

Instead of loading all Kora knowledge for every task, the agent can load a DI skill for graph work, an HTTP client skill for HTTP integration, or a Kafka consumer skill for messaging.

The official Kora skills repository's domain decomposition already points toward this model.

Selective loading is important for scalable agent workflows.

## The Knowledge Stack Can Become a Tooling Surface { #tooling-surface }

Once framework knowledge is structured for agents, other tools can use it too.

For example: IDE assistants, code review bots, migration agents, linting systems, onboarding tutors, and automated refactoring tools.

The skill is therefore not only a chat feature.

It can become part of a broader developer tooling ecosystem.

## Migration Guides Become Especially Important { #migration-guides }

When Kora 2 changes from Kora 1, migration knowledge needs explicit representation.

A human developer can read a migration guide. An agent can apply it systematically across a codebase.

That turns migration documentation into an automation substrate.

The better the migration guide is structured, the more safely agents can transform applications.

This is another example of documentation becoming executable context.

## The Same Applies to Deprecations { #deprecations }

A deprecation message can contain the old API, the replacement API, the behavioral difference, and a migration example.

An agent can act on that immediately.

Framework authors should increasingly write deprecations with automation in mind.

The prose is no longer only informational. It can drive code changes.

## Kora Examples Can Function as Regression Patterns { #regression-patterns }

Canonical examples can also serve as regression patterns.

An agent updating an application can compare its approach to the nearest official example.

If the application's structure diverges unexpectedly, that may indicate legitimate custom architecture, outdated code, or a generated mistake.

The examples become reference implementations for both learning and maintenance.

## AI Can Explain Generated Code Back to the Developer { #explain-generated-code }

Another interesting loop is:

```text
developer writes high-level declaration
        ↓
Kora generates implementation
        ↓
agent reads implementation
        ↓
agent explains it in human language
```

This closes the abstraction gap.

The developer gets the productivity of declarative APIs without losing access to the mechanics.

That is exactly the kind of balance Kora's transparency model is trying to achieve.

## The Framework Can Become Self-Explaining { #self-explaining }

Taken far enough, the combination of docs, generated source, source code, skill, and agent creates a framework that can effectively explain itself.

The developer can ask: "Why did Kora generate this?" and the agent can answer using both framework rules and current project state.

That is a qualitatively different experience from reading a static manual.

## The New Documentation UX Is Conversational but Evidence-Based { #conversational-ux }

There is a risk in describing this as conversational documentation.

Conversation alone is not enough. A generic chatbot can confidently invent framework APIs.

The valuable model is:

```text
conversation
+
canonical retrieval
+
project context
+
compiler validation
+
tests
```

That is evidence-based conversation.

The official Skill helps anchor the conversation in framework truth.

## Authority Matters More Than Fluency { #authority-over-fluency }

AI answers often sound fluent whether they are correct or not.

Therefore the most important property of an agent-based documentation system is authority.

Can the model distinguish official current reference from an old blog or a training-memory guess?

Framework-maintained skills can encode that hierarchy.

This is a significant advantage over purely generic AI assistance.

## The Knowledge Stack Should Have a Clear Precedence Order { #precedence-order }

A sensible precedence could be:

```text
current framework reference
        ↓
current guides
        ↓
current official examples
        ↓
current generated source
        ↓
current framework source
        ↓
community material
```

Generated source may outrank generic prose for application-specific behavior. Framework source may outrank docs when diagnosing implementation details.

The exact order depends on the question.

The important thing is that the agent knows which sources are authoritative for which kind of claim.

## Community Folklore Becomes Less Necessary { #community-folklore }

Mature frameworks often accumulate "things everyone knows" that are difficult to find in official docs.

Examples include proxy self-invocation rules, starter activation surprises, hidden initialization requirements, or version-dependent container behavior.

Such folklore becomes a hidden curriculum.

Kora's compile-time and generated-code approach tries to minimize that category.

In the AI era, this becomes even more valuable because folklore is hard to retrieve reliably.

Explicit code is much easier.

## Documentation Can Compete With Community Size { #compete-community-size }

A small framework will probably never have the same volume of forum posts as Spring.

That no longer means it must lose the knowledge race automatically.

If Kora has high official coverage, current guides, runnable examples, inspectable generated code, open source, versioned agent guidance, and strong compiler diagnostics, then the effective answer
surface can be much larger than the raw community corpus suggests.

This is a significant change in framework economics.

## The Cost of Being New Is Lower Than It Used to Be { #cost-of-new }

Historically, using a newer framework meant accepting fewer Stack Overflow answers, fewer blog posts, fewer experienced hires, and fewer tutorials.

AI reduces some of that penalty.

It cannot invent missing implementation quality or production maturity. But it can dramatically reduce the information-navigation cost when authoritative material exists.

That makes good documentation disproportionately valuable to newer frameworks.

## The Cost of Poor Documentation Is Higher Than It Used to Be { #cost-of-poor-docs }

The reverse is equally important.

A framework with weak documentation may perform worse with AI than with humans because the model fills gaps with plausible guesses.

That can generate subtle incorrect code quickly.

Therefore "AI can read source" is not an excuse to neglect docs. It raises the stakes for canonical knowledge.

## AI Does Not Eliminate the Need for Documentation { #docs-still-needed }

A common mistaken conclusion is:

```text
AI can explain code
therefore documentation matters less
```

The opposite is closer to reality.

AI needs reliable context.

Documentation supplies intended behavior, supported contracts, recommended patterns, semantic guarantees, and version-specific boundaries.

Source code shows what the implementation does. Documentation says what it promises.

Both matter.

## Source and Docs Answer Different Questions { #source-vs-docs }

Consider a timeout default. Source may show the current constant. Documentation should state whether that value is part of the supported contract.

Consider an internal generated class. Source shows its structure. Documentation should explain whether developers may depend on it.

Consider an extension point. Source shows how it works today. Documentation explains how it is intended to be used.

AI agents need both implementation truth and contract truth.

## Guides Preserve Design Intent { #guides-design-intent }

This is why guides remain essential even when an agent can read source.

Source answers "how." Guides often answer "why."

A model can infer intent from code, but explicit guidance is more reliable.

For example: why use OpenAPI first, why prefer typed configuration, why choose `ValueOf`, why keep SQL explicit.

Those are architectural decisions, not merely APIs.

Guides preserve them.

## The Best Knowledge Systems Are Layered, Not Redundant { #layered-not-redundant }

The ideal architecture is not to repeat the same answer six times.

It is to assign different responsibilities:

```text
reference → contract
guide → intent
example → pattern
generated code → current materialization
framework source → implementation
skill → navigation and conventions
compiler/tests → validation
```

That is a mature knowledge system.

Kora is increasingly organized in that direction.

## An Agent Can Turn Documentation Into a Project-Specific Guide { #project-specific-guide }

Suppose a developer joins an unfamiliar Kora service.

Instead of reading the entire framework documentation, they can ask:

> Explain how HTTP requests reach the database in this project.

An agent can combine Kora HTTP docs, the project controller, generated handler, service, generated repository, and database config, then produce a walkthrough specific to that codebase.

The framework docs become the semantic dictionary. The project provides the instance.

This is one of the most useful forms of AI-assisted onboarding.

## Onboarding Becomes Query-Driven { #query-driven-onboarding }

Traditional onboarding often front-loads large amounts of context: read the architecture wiki, read framework docs, watch videos, read examples.

Much of that information is forgotten before it is needed.

AI allows just-in-time onboarding:

```text
question arises
→ agent retrieves relevant canonical context
→ explains current project
```

Kora's small surface and explicit architecture make this especially effective.

## The Same Helps Senior Engineers Too { #senior-engineers }

This is not only for beginners.

An experienced engineer may understand Kora generally but rarely touch S3, SOAP, scheduling, Cassandra, or a specific OpenAPI generator option.

Instead of memorizing every module, they can rely on the knowledge stack.

This reduces the need for framework trivia as professional capital.

## Memory Becomes Less Important Than Reasoning { #memory-vs-reasoning }

This connects to a broader change in software engineering.

When retrieval is cheap, memorizing every annotation or configuration property becomes less valuable.

Understanding transaction semantics, concurrency, failure modes, protocols, and architecture becomes relatively more valuable.

A good framework knowledge system supports that shift.

The agent handles lookup. The engineer handles judgment.

## The Official Skill Can Encode Safe Defaults { #skill-safe-defaults }

One especially valuable role for a skill is preventing the agent from choosing clever but unsupported paths.

For example:

```text
prefer official module
prefer generated repository
prefer current synchronous API
prefer canonical testing approach
```

This can keep generated code aligned with framework philosophy.

Without such guidance, a general-purpose model may import habits from Spring, Quarkus, or Ktor into Kora unnecessarily.

## Framework Cross-Contamination Is a Real AI Problem { #cross-contamination }

Language models have seen many Java frameworks.

They can accidentally mix concepts:

```text
Spring annotation
+
Micronaut assumption
+
Kora package
```

The result can look plausible.

Strong versioned skill guidance is a defense against this.

It tells the model which conceptual world it is operating in.

This is another reason official machine-readable context matters.

## The Skill Can Reduce "Framework Accent" { #framework-accent }

AI-generated code often has an accent from more common ecosystems.

For Java, that accent is frequently Spring-like.

A Kora Skill can reinforce Kora-native patterns: compile-time modules, explicit factories, thin abstractions, generated repositories, `ValueOf`, and Kora testing.

This helps the agent produce code that fits the framework rather than merely compiles.

## Correct Code Is Not Enough; Idiomatic Code Matters { #idiomatic-code }

A general model may find a technically valid Java solution that bypasses the framework.

Sometimes that is fine. Sometimes it creates inconsistency.

Official skill guidance can encode what Kora considers idiomatic.

This is analogous to having a senior framework engineer present during every AI-assisted edit.

## The Skill Is Also a Documentation Maintenance Test { #skill-maintenance-test }

Maintaining an official skill forces framework authors to clarify preferred patterns, stable terminology, version boundaries, and canonical sources.

If the team cannot express these clearly for an agent, the framework knowledge model may itself be ambiguous.

In this sense, writing agent guidance is a useful pressure test for documentation quality.

## Machine-Readable Knowledge Exposes Inconsistency Quickly { #exposes-inconsistency }

An agent traversing many sources may notice contradictions humans rarely connect.

For example:

```text
guide says one default
reference says another
example uses a third
```

This can reveal documentation debt.

The framework team can use AI not only to consume docs but to audit them.

That is another new feedback loop.

## Documentation Testing Can Become Automated { #automated-doc-testing }

A framework can increasingly test its knowledge system.

Possible checks include compiling every code block, running every example, verifying configuration names against source, detecting dead links, comparing documented defaults with code, and running
agent evaluation prompts against canonical answers.

This moves documentation quality closer to software quality engineering.

## Agent Evaluations May Become Part of Framework CI { #agent-evaluations-ci }

Imagine Kora maintaining evaluation questions such as:

```text
Create JDBC repository with transaction.
Explain ValueOf refresh behavior.
Create HTTP client with custom response mapper.
Replace component in a test.
```

A test harness could run an agent with the official skill against a sample project and verify that the result compiles.

This is a natural extension of documentation-as-executable-context.

The framework can test not only whether humans can read the docs, but whether agents can apply them correctly.

## Framework Documentation Becomes an Interface { #docs-as-interface }

This leads to a stronger conceptual claim:

**Documentation is increasingly part of the framework's API surface.**

Not in the binary compatibility sense. In the operational sense.

Developers and agents depend on it to produce correct code.

A stale documentation page can therefore be almost as damaging as a bad API.

That raises the bar for maintenance.

## The Knowledge Interface Has Multiple Consumers { #interface-consumers }

The same canonical Kora knowledge can serve a human developer, AI coding agent, IDE assistant, code review bot, migration tool, onboarding tutor, and support bot.

This multiplies the value of every improvement to documentation structure.

A well-written guide is no longer only a page. It is reusable machine context.

## The Old "More Content" Strategy Becomes Less Attractive { #more-content-strategy }

Framework communities historically gained visibility by producing huge amounts of blogs, answers, talks, and tutorials.

That still has marketing and educational value.

But for reliable AI-assisted development, a smaller canonical corpus can be more valuable than a giant decentralized archive.

The optimal strategy changes from:

```text
maximize volume
```

to:

```text
maximize authoritative signal
```

Kora's compact documentation philosophy aligns with this shift.

## Historical Archives Can Become Noise { #historical-archives-noise }

A framework with 15 years of community content has enormous knowledge capital.

It also has enormous archaeological complexity.

Old configuration keys remain indexed. Deprecated APIs rank highly. Answers assume old JDKs. Blog posts describe old execution models.

AI agents must filter aggressively.

This is a real cost of maturity.

It does not erase the benefits of a mature ecosystem, but it complicates retrieval.

## A Younger Framework Can Start With AI-Native Knowledge Hygiene { #ai-native-hygiene }

Kora has an opportunity to avoid some of that debt.

It can design from the beginning around versioned docs, explicit migration guides, current canonical examples, versioned skills, dense references, and readable generated source.

That is easier than cleaning up 15 years of conflicting material later.

In this sense, being younger can be an advantage if the knowledge system is designed intentionally.

## Kora's 95% Claim Should Be Read as Coverage, Not Volume { #coverage-not-volume }

The meaningful part of the "95%+" statement is not the number of words.

It is the claim that most framework functionality has a canonical explanation somewhere in the official knowledge system.

That is the correct goal.

A feature with 30 pages of vague explanation is not better documented than a feature with one precise reference page, one guide, and one working example.

Coverage is about answerability.

## Answerability Is the New Documentation KPI { #answerability-kpi }

A useful new KPI is:

> Can a developer or agent answer the important operational questions about this feature from official material?

For each module:

- how do I enable it?
- how do I configure it?
- how do I use it?
- how do I test it?
- how does it fail?
- how do I observe it?
- how do I extend it?
- where can I inspect generated behavior?

If those answers exist, the feature is genuinely documented.

## The Agent Can Surface Missing Documentation { #surface-missing-docs }

When an agent repeatedly has to inspect source because a contract is absent from docs, that is a signal.

Framework teams can use agent traces to identify common retrieval failures, ambiguous pages, missing examples, and undocumented defaults.

This creates a new feedback channel from documentation consumption.

## Support Questions Can Improve Canonical Knowledge Directly { #support-improve-knowledge }

Historically, a support answer might remain in a chat or GitHub issue.

In a machine-readable knowledge model, recurring questions should be promoted into a reference clarification, guide section, example, or skill instruction.

That prevents the same ambiguity from recurring.

The knowledge system becomes self-improving.

## The Skill Can Point to Generated Sources, Not Just Docs { #skill-generated-sources }

One of the most Kora-specific possibilities is teaching agents to inspect generated source deliberately.

For example:

```text
If dependency wiring is unclear:
inspect generated application graph.

If repository mapping is unclear:
inspect generated repository.

If AOP ordering is unclear:
inspect generated subclass.

If HTTP mapping is unclear:
inspect generated handler.
```

This is a powerful agent workflow because the framework already generates readable code.

Not every framework can offer this escalation path cleanly.

## Generated Code Becomes an Official Debugging Surface { #debugging-surface }

This should be treated as intentional product design.

If generated source is part of how humans and AI debug the framework, then its readability matters.

Variable naming matters. Class structure matters. Stack traces matter. Source mapping matters.

The generated artifact is not merely a compiler implementation detail.

It is part of the developer experience.

## Compiler Feedback and Generated Code Reinforce Each Other { #compiler-generated-reinforce }

Suppose compilation fails while generating a mapper.

The diagnostic tells the agent what is missing.

The generated partial source or neighboring generated classes show the expected pattern.

The docs explain the supported mapping model.

Together they triangulate the solution.

This is exactly what a rich knowledge stack should do.

## The Knowledge Stack Can Shorten the Support Loop { #shorten-support-loop }

Traditional framework support may look like:

```text
developer posts question
      ↓
maintainer asks for reproducer
      ↓
developer clarifies
      ↓
maintainer explains
```

With an agent and strong official context:

```text
developer asks locally
      ↓
agent inspects code/docs/generated source
      ↓
compiler confirms
      ↓
many questions resolved before support request
```

This can reduce maintainer load.

A smaller framework benefits disproportionately from that.

## Maintainer Bandwidth Becomes More Scalable { #maintainer-bandwidth }

A large framework can rely on a large community support network.

A smaller framework has fewer people answering questions.

An official agent knowledge layer can partially scale maintainer expertise.

It cannot replace maintainers for bugs and deep design questions, but it can handle repetitive "how do I" questions very efficiently.

That makes small framework ecosystems more viable.

## Official Skills Can Encode Maintainer Intent Directly { #maintainer-intent }

Community-trained AI may know what users often do.

An official Skill can know what maintainers recommend.

Those are different.

The most common workaround on the internet may not be the intended solution.

Machine-readable maintainer intent helps keep generated code aligned with the framework's design.

## The Best Knowledge System Minimizes Lore { #minimizes-lore }

Kora's broader philosophy is relevant here.

A framework that requires developers to memorize hidden rules creates knowledge that is difficult to encode reliably.

A framework whose behavior is visible in types, generated code, compiler errors, and explicit modules has less lore.

That makes the official knowledge system smaller and more complete.

The architecture itself reduces documentation burden.

## Less Runtime Magic Means Less Documentation About Magic { #less-runtime-magic }

Every invisible runtime mechanism requires explanatory material.

For example:

```text
when proxy applies
when proxy does not apply
how self-invocation behaves
what order interceptors run
how conditional registration works
```

If the mechanism becomes generated source, some of that explanation becomes inspectable.

Documentation can focus more on intent and contract.

This is another way architecture and documentation interact.

## Strong Typing Is Also Knowledge Encoding { #strong-typing }

Types themselves carry documentation.

Consider:

===! ":fontawesome-brands-java: `Java`"

    ```java
    ValueOf<Client>
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    ValueOf<Client>
    ```

That communicates something different from:

===! ":fontawesome-brands-java: `Java`"

    ```java
    Client
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    Client
    ```

A model can infer lifecycle semantics from the type once the concept is documented.

Likewise, `All<T>`, tags, configuration source interfaces, and repositories encode structural meaning in source.

Strong typing therefore makes the application more self-describing.

That helps both IDEs and agents.

## The Project Itself Becomes a Knowledge Base { #project-knowledge-base }

Once source, generated code, build files, tests, and configuration are machine-readable, the current repository becomes part of the documentation system.

The agent learns local conventions, module composition, naming, existing integrations, and test style.

Official Kora knowledge gives the grammar.

The project gives the dialect.

This combination produces much better answers than either source alone.

## The Framework Skill Should Respect Project Conventions { #respect-project-conventions }

Official guidance should not blindly overwrite local architecture.

A good agent uses the Skill to understand Kora, then reads the project to understand the team's choices.

For example, an official Kora recommendation plus a project already standardized on a slightly different local pattern may produce a different answer than a greenfield project.

The knowledge stack therefore supports adaptation rather than rigid code generation.

## AI-Assisted Development Is Not About Removing Engineers { #not-removing-engineers }

The strongest use of this system is not replacing human judgment.

It is removing low-value navigation work.

The agent can find the right reference, reconcile several pages, locate the nearest example, adapt boilerplate, inspect generated code, compile, and run tests.

The engineer can focus on whether the architecture is correct, whether the semantics are safe, and whether the production trade-off is acceptable.

That division is productive.

## Documentation Becomes Part of the Feedback Loop { #feedback-loop }

The full Kora development loop can now be described as:

```text
question
  ↓
official knowledge retrieval
  ↓
project-specific generation
  ↓
compile-time validation
  ↓
generated-source inspection
  ↓
test execution
  ↓
refinement
```

Documentation is not outside development anymore.

It is one stage inside the loop.

That is the central transformation.

## This Changes What "Developer Experience" Means { #developer-experience }

Traditional DX metrics included API ergonomics, documentation clarity, startup time, build time, and debugging.

AI-era DX adds agent retrievability, source explainability, diagnostic precision, canonical examples, machine-readable conventions, and versioned skills.

A framework can be pleasant for humans but difficult for agents.

Kora's design tries to make the same properties serve both.

## Human-Friendly and AI-Friendly Design Are Surprisingly Similar { #human-ai-friendly }

The overlap is substantial.

Humans like explicit architecture, few abstractions, good names, precise errors, readable generated code, and clear docs.

Agents like exactly the same things.

This is why Kora's AI fit can be described as a consequence of human-oriented design rather than an AI-specific retrofit.

The documentation system follows the same pattern.

## A Knowledge Stack Is Stronger Than a Knowledge Base { #stack-vs-base }

A knowledge base stores information.

A knowledge stack combines:

```text
information
+
implementation
+
retrieval
+
validation
```

That is the conceptual upgrade.

Kora's emerging system includes all four.

Documentation and guides store information. Examples and source provide implementation. Skills and agents provide retrieval and adaptation. Compiler and tests provide validation.

This is why "documentation" no longer feels like a sufficient word.

## The Old Metric Is Becoming Obsolete { #old-metric-obsolete }

The historical framework comparison:

```text
Framework A:
200,000 Stack Overflow questions

Framework B:
2,000 questions
```

still tells us something about community history.

But it no longer tells us the whole support story.

A better modern comparison is:

```text
How complete are official sources?
How current are they?
Can the agent retrieve them?
Can examples be executed?
Can implementation be inspected?
Can mistakes be validated automatically?
```

A smaller corpus can compete if those answers are strong.

## The New Metric: Reliable Derivation { #new-metric-derivation }

The best summary is:

> **In the AI era, the best-documented framework is not necessarily the one with the largest archive. It is the one whose authoritative knowledge is complete, structured, current, machine-readable,
and easy for both humans and agents to reason about.**

This does not reward minimal documentation.

It rewards *high-quality derivability*.

Can the correct answer be constructed reliably?

That is what matters.

## Kora's Documentation Model Fits This New Metric { #kora-fits-new-metric }

Kora's current direction combines:

```text
95%+ claimed functionality coverage
        +
step-by-step guides
        +
module references
        +
runnable kora-examples
        +
human-readable generated source
        +
open framework source
        +
official kora-skills repository
        +
compile-time diagnostics
        +
fast tests
```

No single item is revolutionary alone.

Together they form a coherent machine-readable environment.

That combination is much more interesting than page count.

## The Official Skill Is the Missing Interface Layer { #skill-interface-layer }

Without the Skill, the agent still has to discover the knowledge architecture itself.

With the Skill, the framework can teach the agent how to navigate it.

That closes the loop:

```text
framework authors
      ↓
canonical sources
      ↓
versioned skill
      ↓
agent
      ↓
developer
```

This is effectively framework-maintained context injection.

It is a new kind of developer API.

## The Current Kora Skill Is a Beginning, Not the End { #skill-beginning }

Because the current package targets Kora 1.x, the natural next step is obvious: Kora 2 needs version-specific agent guidance that reflects its current architecture.

That is not a weakness of the idea.

It is evidence that the idea is being treated seriously.

AI guidance should evolve with the framework.

A generic timeless skill would be less trustworthy.

Versioning is the correct architecture.

## A Future Kora 2 Skill Can Encode the Whole Modern Model { #future-kora2-skill }

A Kora 2 package can eventually encode guidance around synchronous virtual-thread execution, Kora 2 DI rules, repository model, HTTP and OpenAPI, runtime graph refresh, current telemetry contracts,
scheduling, resilience, current testing model, and generated-source inspection.

That would give agents a framework-native entry point to the entire Kora 2 knowledge stack.

The Kora 2 landing page already presents this direction as part of the developer experience.

## The Framework Website Can Become the Human View of the Same Knowledge { #website-human-view }

Another interesting possibility is convergence.

The same structured canonical material can power:

```text
human docs website
agent skill
IDE assistant
CLI help
support bot
```

Instead of maintaining separate inconsistent knowledge bases, the framework can expose multiple interfaces over one source of truth.

That is a much more maintainable long-term architecture.

## Canonical Knowledge Should Be Reusable by Design { #reusable-by-design }

Documentation authors should therefore think in reusable units: one authoritative concept definition, one canonical configuration table, one runnable example, one migration rule.

Different surfaces can reference those units.

This reduces duplication and drift.

It also makes retrieval more precise.

## AI Will Increase Pressure for Documentation Schema { #documentation-schema }

Over time, frameworks may formalize knowledge more structurally.

For example, module metadata, supported annotations, configuration schema, generated artifact types, lifecycle semantics, and examples could become machine-readable beyond Markdown.

Kora already has strong typed configuration and compile-time metadata internally, so some of this structure already exists in code.

The documentation layer can increasingly expose it.

## Not Everything Should Become Structured Data { #not-structured-data }

Narrative still matters.

Architecture, trade-offs, and design reasoning are difficult to reduce to schemas.

The best knowledge stack will combine:

```text
structured facts
+
narrative reasoning
+
executable examples
```

Again, different layers serve different needs.

## The AI Era Rewards Frameworks That Know What They Are { #frameworks-know-themselves }

A framework with unclear identity creates unclear guidance.

If every problem has several equally official solutions, a Skill cannot confidently recommend one.

Kora's strong opinions make its machine guidance easier to define.

This is a subtle but important advantage.

AI amplifies the value of a coherent framework philosophy.

## Kora's "One Problem, One Solution" Becomes a Knowledge Architecture { #one-problem-one-solution }

The principle is no longer only about coding style.

It affects documentation organization, example design, agent retrieval, generated code, and compiler diagnostics.

One canonical path creates a cleaner knowledge graph.

That can improve both human onboarding and autonomous coding.

## Fewer Abstractions Mean Fewer Documentation Edges { #fewer-abstractions }

Imagine every abstraction as a node and every interaction as an edge.

A framework with many overlapping abstractions produces a dense graph of combinations that must be documented.

A framework with a smaller orthogonal set has fewer combinations.

This reduces the total documentation burden.

It also reduces the number of interaction cases an AI agent must learn.

This is a structural advantage, not merely a stylistic preference.

## Documentation Coverage Can Scale Better Than Framework Surface { #coverage-scales }

This explains an important Kora claim.

A framework with fewer features can achieve higher documentation coverage more realistically.

The goal is not to boast that the documentation repository is larger.

It is to keep the ratio:

```text
documented behavior
-------------------
framework behavior
```

high.

For agents, this ratio matters more than raw page count.

## The Knowledge Stack Makes Small Ecosystems More Competitive { #small-ecosystems }

A smaller framework normally suffers from a smaller support corpus.

Kora's approach changes the equation:

```text
smaller community corpus
        ↓
offset by
        ↓
higher official coverage
+
runnable examples
+
inspectable implementation
+
agent skill
+
compiler feedback
```

This does not fully replace community scale.

But it reduces dependence on it.

That is strategically important.

## The Framework Can Answer Questions Nobody Has Asked Before { #answer-novel-questions }

This may be the most important AI-era capability.

Suppose nobody has ever published:

> How do I combine Kora configuration refresh, two tagged HTTP clients, and a custom retry mapper in this exact architecture?

Traditional search has no exact result.

An agent can still reason from config docs, tag docs, HTTP client docs, resilience docs, examples, project source, and generated graph, then derive the implementation.

That is new.

It changes the relationship between documentation completeness and community history.

## Novel Questions Become Compositional Questions { #compositional-questions }

Instead of requiring one stored answer per possible problem, the framework needs high-quality primitives.

This is analogous to software itself.

You do not need a function for every possible application. You need composable APIs.

Similarly, documentation can provide composable knowledge primitives.

AI performs the composition.

Kora's modular documentation structure supports this naturally.

## The Framework Knowledge Stack Mirrors the Framework Architecture { #mirrors-architecture }

There is a pleasing symmetry here.

Kora's code philosophy is:

```text
small explicit components
+
composition
```

Its ideal knowledge philosophy is:

```text
small authoritative knowledge layers
+
composition
```

The agent combines them just as the framework combines components.

This consistency makes the system easier to reason about.

## Documentation Should Become a First-Class Release Artifact { #first-class-release }

The final organizational implication is straightforward.

For an AI-assisted framework, releasing code without synchronized documentation, examples, and skill guidance becomes increasingly unacceptable.

A complete release should eventually mean:

```text
framework binaries
documentation
guides
examples
migration notes
agent guidance
```

All version-aligned.

That is the new standard Kora is moving toward.

## Conclusion: Documentation Has Become an Interactive System { #conclusion }

Framework documentation used to be a destination.

A developer left the code, opened a browser, searched for information, interpreted it, returned to the project, tried an implementation, and repeated the cycle until something worked.

That model still exists, but it is no longer the whole experience.

In an AI-assisted workflow, framework knowledge can sit directly inside the development loop.

A developer asks a question in the context of the real application. The agent can consult official reference documentation, load a guide, inspect the nearest runnable example, read the application's
handwritten source, open Kora's generated implementation, inspect framework source when necessary, write the change, compile it, read precise diagnostics, run tests, and refine the result.

That is not just documentation search.

It is interactive knowledge application.

Kora is especially well suited to this model because the same architectural properties that make the framework transparent to humans also make its knowledge machine-readable: a small conceptual
surface, strong types, readable generated code, compile-time diagnostics, explicit modules, runnable examples, and a deliberate separation between reference documentation and deeper guides.

The official Kora Skills project adds another important layer. It gives coding agents a framework-maintained way to understand Kora concepts and navigate canonical sources. The current published
package is explicitly versioned for Kora 1.x, while the Kora 2 documentation already presents the skills repository as part of the broader AI-assisted developer experience. That version boundary is
important rather than inconvenient: agent guidance should track framework generations just as carefully as API documentation does.

The result is a new model:

```text
Official reference
        +
Guides
        +
Runnable examples
        +
Application source
        +
Generated source
        +
Framework source
        ↓
Versioned Kora Skill
        ↓
AI agent
        ↓
Context-specific explanation
        ↓
Project-specific implementation
        ↓
Compiler + tests
```

This is the **Kora Knowledge Stack**.

Each layer has a clear responsibility. Reference material provides facts. Guides preserve reasoning and workflows. Examples demonstrate canonical patterns. Generated source shows what Kora did in the
exact application. Framework source provides implementation truth. The Skill provides retrieval strategy and framework conventions. The compiler validates structural assumptions. Tests validate
behavior.

That model also changes how documentation quality should be measured.

The old question was:

```text
How much documentation exists?
```

or even:

```text
How many answers about this framework exist on the internet?
```

Those metrics still tell us something, but they increasingly miss the important property.

The better question is:

> **How much authoritative context can an agent reliably use to solve a developer's actual problem?**

This favors documentation that is current, dense, structured, versioned, consistent, and executable through examples. It also favors frameworks with one recommended path and little hidden runtime
behavior, because ambiguity is expensive for both humans and machines.

A giant historical archive can be extremely valuable, but it can also contain obsolete APIs, conflicting generations, community folklore, duplicated explanations, and patterns that were correct five
years ago but are wrong today. AI does not magically eliminate that problem. In some cases it amplifies it.

A smaller canonical knowledge base can therefore compete surprisingly well if an agent can reliably compose its pieces.

This leads to the broader conclusion:

> **A framework no longer needs a historical answer for every possible question if its authoritative sources are complete enough for an agent to derive the answer.**

And that gives us a new definition of what it means to be well documented:

> **In the AI era, the best-documented framework is not necessarily the one with the largest archive. It is the one whose authoritative knowledge is complete, structured, current, machine-readable,
and easy for both humans and agents to reason about.**

Kora's documentation model is increasingly moving in that direction. It is not merely a set of pages explaining APIs. It is becoming a complete knowledge system: concise reference material, deeper
guides, runnable examples, inspectable generated code, open framework source, compiler feedback, tests, and an official agent skill that gives AI tools a canonical path into that material.

The final shift can be summarized in two lines.

The old metric was:

> **How many answers about this framework exist on the internet?**

The new metric is:

> **Can an agent reliably derive the right answer from authoritative sources?**

That is a much more demanding standard.

It is also a much more useful one.
