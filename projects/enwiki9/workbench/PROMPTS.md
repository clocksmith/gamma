# Workbench prompts

Use the system prompt with one task. Replace bracketed names with actual
candidates or questions. Commands run from `gamma/projects/enwiki9/`.

**System prompt**

```text
Operate the enwiki9 research workbench under the applicable AGENTS.md/CATSCAN.md
instructions. Read ADAPTIVE_WORKFLOW.md for commands and ledger/README.md for
canonical records. Begin with tools/enwiki9_lab.py start; retrieve relevant
evidence through records, including the tool catalogue before writing utilities.
Retrieve the chosen mechanism's reflection history; state which recorded lesson
the next experiment applies or which unresolved uncertainty it tests.
At a closed-result or independent-work decision boundary, apply the manual's
Choose Testing, Mutation, Or Exploration rules. When exploration is indicated,
use Creative discovery below and finish one selected executable gate or a
specific evidence-backed rejection before generating more alternatives.
Design and implementation can proceed with local tools and independent agent
review. External model consultation is optional and creates no prerequisite.
Carry the user's question through the smallest justified executable comparison
or research decision. Preserve existing ownership, source identities, and evidence
bindings. Use the canonical lifecycle and standing bounded-work permissions.
Record the outcome, its limitations, and the next concrete action with source
links. Follow the active objective contract; historical values remain historical.
```

**Go**

```text
Go. Inspect current work, ownership, selected ancestry, and dependencies. Resume
the next justified action. Resolve a held gate's named blocker or advance
independent work. Carry the action to a recorded result or evidence-backed handoff.
```

## Creative discovery

Use this cycle when the [decision rules](../ADAPTIVE_WORKFLOW.md#choose-testing-mutation-or-exploration)
call for exploration. These are design perspectives an agent can combine in its
own reasoning. They do not require separate agents or external models. The role
files under `agents/` specialize this shared loop; `dac_crackpot.md` is a
historical adversarial fixture and is excluded from discovery selection.

Select two synthesis lenses below. For codec discovery, default to lenses 1-10;
use 11-12 when a measured experiment bottleneck justifies infrastructure work.
Choose deliberately when a measured failure suggests a direction; otherwise
sample without replacement using a recorded seed, such as the prospective
proposal ID:

```bash
python3 -c 'import random; seed="PROPOSAL-ID"; print(random.Random(seed).sample(range(1, 11), 2))'
```

Record the seed, selected IDs, and chosen premise in the existing register entry
or proposal explanation. Avoid repeatedly drawing until a familiar idea returns.
A lens may be inapplicable; record why and choose a replacement. Historical
portfolios are idea sources whose old rankings and exclusions need current
evidence review. They do not determine the next launch.

The names below are inspiration and retrieval terms from the supplied concept
menu, with repeated entries consolidated. They are not verified descriptions,
compatibility guarantees, or current candidate verdicts. Verify an external
method's primary paper, implementation, and license before adopting it; resolve
Gamma names through the ledger and their scoped reflections.

| ID | Synthesis | Implementable exploration prompt |
| --- | --- | --- |
| 1 | AlphaGeometry-style propose-and-check + LOGOS/FRACTAL-2 + graph reduction | Propose reusable byte programs, then admit a rule only when a symbolic expansion check proves the required exact output. Can parameterized templates and shared arguments pay for their definitions? Compare literal-only, recursive-phrase, and parameterized modes. Preserve emitted bytes and argument bindings when reducing the graph; reachability alone is insufficient. |
| 2 | PALIMPSEST/CMEM + TESSERA + ConceptMoE | Separate a candidate latent concept or structural role from exact surface bytes. Can routes be marginalized from decoded context, or must their IDs be transmitted? Preserve morphology, spelling, whitespace, entities, and exceptions. Compare against shuffled associations and an untyped baseline; measure route and surface costs together. |
| 3 | WIKI-LOOM/Fiber-CTS + NOEMA + feature hashing + hierarchical memory | Build one bounded bank of causal field-history states with shared parameters. Test whether a hierarchy or hashed contexts preserve useful distant information cheaply. Specify collision behavior, memory ceilings, initialization, and state updates. Compare against identical capacity without semantic routing. |
| 4 | Cross-model cache alignment + latent-state transfer + SAFE-FORK/ANCHOR-MIDAS + tree verification | Translate or branch predictive state using only decoder-available information. Treat exact state compatibility as an open question. Test one synchronized speculative branch, authoritative-parent rejoin, and sham-transfer control. Count any transmitted state and verify probabilities, optimizer/cache state, and coder state at every required boundary. |
| 5 | HORIZON-LOCKSTEP/SABLE/HELICAL + SRSTC + temporal retrieval | Search for causal alignment corridors or continuation reliability beyond a failed exact-match configuration. Can the decoder reconstruct the same donor and stopping rule, or must pointers and skips be paid? Use appropriate causal warmup and shifted-donor controls. Preserve live HORIZON and its frozen decision; do not revive Fiber-FOSSIL unchanged. |
| 6 | ARIADNE/REVLOG + RADIX-ISLAND + TWINSTREAM/Route E | Challenge coding order or field representation while preserving exact original order. Price slot maps, numeric exceptions, copied spans, and every parent update. Compare with an equivalently framed baseline using the same backend; require native archive savings before crediting deleted or rearranged bytes. |
| 7 | MOIRAI + parity-game decomposition + subset transforms | Formulate a finite constraint-decoding problem: transmitted constraints plus a deterministic bounded search identify exact bytes. Prove uniqueness or encode disambiguation. Can decomposition or subset-state reuse reduce search cost without hiding choices? Start with an exhaustively enumerable toy problem and a literal fallback whose full cost is counted. |
| 8 | GAMMA-MIDAS-CORE/DELTA-MIDAS + CURVATURE/FD-JVP + route fast weights | Use measured state or tensor ablations to select one compact adaptation mechanism. Separate full-model midpoint updates from output-only approximations; do not inherit their gains. Specify causal truths, rebuilds, and deterministic arithmetic. Compare parent, bookkeeping, treatment, and misaligned-truth control with complete synchronization evidence. |
| 9 | SAFE-MIX/SWITCHBOARD + SIBYL/WIKI-JOINT + JANUS/KAIROS | Seek a decoder-visible regime where one specialist adds information the parent misses. Measure a causal mixture or paid selector against matched and shifted controls. State the exact comparator of any regret bound, then account for finite-coder overhead and package cost. Test one joint archive instead of adding component savings. |
| 10 | Exact-residual packing + self-compacting grammars + content-addressed custody | Compress the representation of weights, tables, rules, or repeated package assets while restoring their exact bits. Test sharing and prediction across those objects, counting metadata and restoration code. Require parameter hashes and probability-stream identity. Distribution caches or shared custody do not remove required decoder bytes from the submitted package. |
| 11 | Recursive GEPA-style mutation + three-loop coordination + retrieval and rejected-hypothesis memory | Use prior receipts to propose a better next experiment. Combine semantic, temporal, and anticipatory retrieval; let old failures supply counterexamples. Test the scheduling idea on a fixed historical replay with future outcomes hidden. Decay retrieval priority, never erase canonical evidence. Judge valid gates and uncertainty resolved per declared compute budget; scheduling improvements earn zero codec credit. |
| 12 | Disagreement replication + canary/hot-swap promotion + proof-carrying job envelopes | Spend verification on the first meaningful disagreement: prediction, state, artifact, or accounting. Design a bounded canary with cancellation, duplicate-delivery handling, and rollback. Hashes, signatures, quorums, and release passports establish specific provenance facts; they do not prove compression quality. Use existing jobs and receipts rather than adding another governance registry. |

Ring allreduce, adaptive peer rings, artifact routers, and model-custody schemes
can inspire bounded experiment distribution or build reuse. Keep that work
separate from the final codec's declared execution envelope. Biological evidence
graphs and human-judgment routing can inspire provenance and contradiction
handling; they add neither automatic scientific truth nor approval prerequisites
beyond the current instructions.

The supplied name `MIDAS-32` covers two different mechanisms: full-model
midpoint learning and a proposed shallow episodic logit correction. Keep their
identities and evidence separate. Likewise, a named family, an implementation,
a failed configuration, and a proposed successor are distinct records.

Combine the two perspectives with this prompt:

```text
Explore using lenses [A] and [B], seed [SEED], and development budget [BUDGET].
Read two relevant prior results when available, including a failure. If evidence
is absent, state that instead of inventing precedent. Use three reasoning passes:
designer proposes a mechanism, decoder implementer reconstructs exact bytes,
and reviewer looks for the smallest falsifying example. These are my own passes;
they are not independent verification.

Generate at most three materially different hypotheses, including one outside
the current family. For each, name the exploited dependence, counted decoder
inputs, expected failure mode, and smallest executable discriminator. Distinguish
measured costs, forecasts, and unknowns. Select one using evidence and cost.
Let the selected lenses change a mechanism, not just its name. State what the
synthesis adds beyond each ingredient alone and what result would falsify it.

Write the chosen hypothesis, parent or standalone baseline, one changed
mechanism, decoder procedure, controls, complete cost categories, population,
resource budget, and stop/next-decision rule into the existing lifecycle.
Use new candidate identity and frozen inputs where required. Implement and test
the smallest admitted gate, or record the specific evidence that rejects it.
Do not finish at an architectural endorsement. Reflect on the result, then
choose testing, mutation, or another exploration cycle from the decision rules.
```

For every mathematical argument, state assumptions and quantifiers: all inputs,
a source average, or this particular corpus. Name the exact coding comparator,
finite precision, termination conditions, and any untransmitted information.
Prove an inverse, overhead bound, or finite search property where applicable;
challenge optimistic gains and overbroad impossibility claims with equal care.
A reviewer must identify missing evidence and the smallest resolving test,
without requiring a full-corpus success before permitting a new idea.

Randomness broadens design choices; it never selects scientific verdicts,
weakens frozen controls, changes live work, or authorizes a larger run.

**Research**

```text
Research [idea or family]. Search prior findings, lineage, mixes, and exclusions.
Identify the information it adds; compare alternatives by savings, package cost,
measured kernel cost, and uncertainty. Cite primary sources and distinguish
external contributions. Record the decision and select a falsifiable experiment.
```

**Create or mutate**

```text
Create [idea or successor] testing [one mechanism]. Freeze its experiment and
development/confirmation boundary, register and seal a unique candidate, then
implement and execute its smallest authorized correctness gate. Preserve the
parent and report the exact artifact, decision, and next missing comparison.
```

**Mix**

```text
Evaluate a mix of [A] and [B]. Record decoder-visible information, shared state,
overlapping costs, and interference in the existing composition graph. Create a
new candidate for an actionable mix and measure its frozen joint comparison.
```

**Benchmark**

```text
Benchmark [candidate] at its smallest justified exact gate. Verify its frozen
bindings, reflections, ownership, and resource envelope; publish ownership and
run the named canonical job. Retain artifacts and record the validated reflection,
run-ledger entry, and research conclusion. Separate diagnostic timing from qualification.
```

**Simulation or proxy**

```text
Test [question] with a bounded simulation or proxy. Freeze population, controls,
outputs, resources, and numeric decision conditions. Use the canonical tool queue
with diagnostic, infrastructure, or oracle purpose. Record units and limitations,
the reflection and conclusion, and the next exact gate. Claim zero score credit.
```

**Review and record**

```text
Review terminal job [job ID]. Verify bindings, output authority, reconstruction,
repeatability, controls, accounting, and resources. Evaluate its frozen predicates
and record or validate the reflection. Preserve failures at their actual cause.
Check the run row, update the research conclusion, and refresh generated views.
```
