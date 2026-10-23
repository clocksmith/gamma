# Research mapping: proposals, not implemented comparisons

[Return to experiment index](INDEX.md). Sources checked 2026-10-20.
Current organization: [goals v2](../contracts/algorithm_solver_goals_v2.json);
[scorecard](../STATUS.md#current-v2-scorecard). Historical numbered goals retain v1 meanings.

Our descriptive formulation is **joint semantics-preserving program rewriting
and bounded static-dictionary compression**. This is a mapping of the existing
problem to related work, not a novelty claim, a new experiment, or a claim that
Gamma implements the cited systems. The exact
[79-literal and 140-literal packages](pass2/working/packages/summary.json) are
preserved controls for the newer [literal-budget comparison](budgets/README.md).

| Question | Related primary source | Relevance and boundary |
|---|---|---|
| Choose strings to minimize selections for fixed text | [Whittington et al., Tokenisation is NP-Complete](https://aclanthology.org/2025.acl-long.1365/) | The paper distinguishes direct vocabulary selection from bottom-up merge selection. We map the fixed-source inner problem to direct tokenisation. Our fixed-dictionary segmentation is exact DP; our vocabulary construction is heuristic. Do not transfer hardness claims indiscriminately to a fixed dictionary. |
| Charge both stored strings and encoded programs | [Casel et al., On the Complexity of the Smallest Grammar Problem over Fixed Alphabets](https://link.springer.com/article/10.1007/s00224-020-10013-w) | The paper analyzes one-level grammars, including rule-count restrictions. Our weighted/cardinality-bounded interpretation additionally charges actual UTF-8 strings, fixed-width IDs and headers across multiple programs. It is a related formulation, not an assertion that their theorem exactly models our wire format. |
| Jointly rewrite equivalent programs and discover reusable structure | [Cao et al., babble](https://arxiv.org/abs/2212.04596) | Library learning modulo theory uses a supplied equational theory, e-graphs/equality saturation and anti-unification. It is the closest listed conceptual comparison to the outer rewrite/library search. Parameterized abstractions differ from our flat literals. Our guarded AST patterns are not babble or a general equivalence engine. |
| Learn a syntactic library from a program corpus | [Bowers et al., Stitch](https://arxiv.org/abs/2211.16605) | Corpus-guided top-down synthesis with syntactic pattern matching is a proposed library-learning comparator. It is not our implemented pair-merging algorithm. |
| Learn libraries and subsequently synthesize task solutions | [Ellis et al., DreamCoder](https://arxiv.org/abs/2006.08381), [Grand et al., LILO](https://arxiv.org/abs/2310.19791) | DreamCoder jointly grows abstractions and a learned search model. LILO combines synthesis, Stitch-based compression and documentation. They inform a later autonomous task-solving track; they provide no evidence that our offline encoded sequences solve autonomously. |
| Practical bounded fixed-string compression | [Boncz et al., FSST](https://www.vldb.org/pvldb/vol13/p2649-boncz.pdf), [author implementation](https://github.com/cwida/fsst) | FSST maps 1–8-byte strings to byte codes and permits escaped raw bytes. Our literals have no such length cap and no free raw-source escape. A fair comparator must retain and charge those differences. [Pinned FSST comparison](fsst-compare-v1/README.md) now measures the author encoder, optimal native parsing and Gamma adapters separately on consumed development sources; it is not M5 qualification. |
| Improve parsing under a learned symbol table | [Chehaidar et al., OptFSST](https://arxiv.org/abs/2607.11271v3) | Optimal dynamic-programming encoding given a table is separated from heuristic table learning. That distinction also matters here. This is a proposed comparator, not an implemented result or evidence of identical formats. |
| Give fixed source pieces structural metadata | [ESTree specification](https://github.com/estree/estree), [Yin & Neubig, syntax-driven code generation](https://aclanthology.org/P17-1041/) | AST metadata and syntax-constrained generation are established tools. Metadata must not insert missing source or imply semantic correctness; the neural paper does not establish Gamma's non-autoregressive goal. |
| Compose functional building blocks | [Balog et al., DeepCoder](https://www.microsoft.com/en-us/research/publication/deepcoder-learning-write-programs/) | Learned guidance for program search from input/output examples is a useful comparator. It does not establish that functional JavaScript rewrites use fewer literal selections or preserve execution cost. |
| Rank partial assemblies or source/library proposals with learned energy | [Gladstone et al., Energy-Based Transformers](https://arxiv.org/abs/2507.02092), [Dai et al., ALOE](https://proceedings.neurips.cc/paper_files/paper/2020/hash/7612936dcc85282c6fa4dd9d4ffe57f1-Abstract.html) | Proposed neural search guidance under v2:4c and v2:2b; see the [bounded comparison proposal](RESEARCH_LOOP.md#proposed-energy-guided-search-goals-v24c-and-v22b). Energy is not correctness, exact encoding cost or an optimality bound. No Gamma implementation or training result is claimed. |

Searching equivalent source variants for a cost objective is also related to
superoptimization in the broad sense. That conceptual relationship does not
establish equivalence of methods, novelty of this combination, or semantic proof
for our JavaScript transformations. Existing outputs are supported by explicit
domain arguments and finite correctness/input-preservation tests.

## Behavior-preserving joint composition

This is current goal **2b**, mapped from the joint-optimization part of legacy
3a. It does not replace human-readable or compression-first policies under 2a. Its target is a shared
vocabulary that constructs programs satisfying complete problem contracts.
The successor may use a different algorithm, data structure, naming scheme or
control flow; it need not reproduce the predecessor's source bytes. Exact
literal decoding still reconstructs every byte of the **selected successor**,
whose hash binds it to its own qualification receipt. Fixed-source reconstruction
remains a separately identified control and keeps its original evidence.

Compression-first may choose arbitrary exact fragments. Human-readable favors
recognizable complete lines, statements, blocks and fully counted reusable
general functions/classes. Both policies can use qualified successor programs;
readability does not replace compression. Abstract common constructs must become
counted source pieces and calls in this flat-literal lane. Typed holes, hidden
operands or nonterminal expansion change the representation and stay separate.
Current whole-solution exclusions remain; a complete task-specific entrypoint or
whole algorithm body is not a general helper merely because it is a function.

**Implemented versus missing.** [joint-v1](joint-v1/README.md) already reselects
among hash-pinned qualified alternatives after exact add/delete/swap/paired
moves; its source loader verifies qualification and matched interfaces. That
experiment made zero accepted source switches, not zero implementation of source
choice. [rewrite-v1](rewrite-v1/README.md) adds bounded capture-checked naming and
existing qualified helper alternatives, with 12 source switches in its measured
joint moves. These are concrete source/dictionary methods, not a general
behavior-equivalence engine. Broad automatic alternative-algorithm generation,
independent qualification at scale, and autonomous description-to-program
assembly have not been established. Stored-answer lookup (1a/1b) is separate.

**Qualification before vocabulary credit.** Pin the full input domain and
observable contract, including outputs and ordering, mutation/alias rules,
numeric/Unicode/exception behavior, and required time/space complexity. Preserve
original sources and qualify each successor separately in the existing approved
isolated judge, using independently established expectations and independent
review. Differential checks against a valid predecessor can help but do not
replace the contract or complexity argument. Mutation, alias and numeric
requirements come from the pinned problem contract, not incidental behavior of
one reference implementation. Retain counterexamples and failed versions; repair and requalify a new version without filtering failures or
weakening requirements. Finite tests establish bounded evidence, not universal
semantic equivalence. An alternative algorithm is permitted only when it meets
these obligations, including any explicitly required observable mutation/order.

**Matched six/seven/eight-bit comparison.** Extend the existing
[baseline protocol](BASELINE_PROTOCOL.md), without rewriting its historical run,
to 64/128/256-entry arms on the same admitted development problems and the same
qualified variants. Freeze cases, source/candidate pools, codebooks, objectives
and compute budgets. Within each candidate policy, give all widths and
source-only/dictionary-only/joint ablations the same information. Treat a change
of candidate policy or mining budget as an explicit factor. Freeze stable IDs
per language/profile; unused IDs fail closed. The old mandatory 96-character
basis cannot fit a 64-entry arm: use an explicitly declared basis and
reachability-aware scoring, rather than silently omitting unencodable programs.
This note does not claim that the canonical joint-v1 implementation already
supports that smaller configuration.

Report coverage with all failures in the denominator; total/median/p95/worst
selections; payload, padding, framing and control bits; stored dictionary,
helpers/imports, full decoder and runtime costs; distinct-problem reuse and
large one-off chunks; correctness/effect/complexity evidence; search time and
memory. Every operand, binding, wrapper and whitespace byte is charged in the
selected encoding. No free adapters, raw-source escapes, hidden dispatch or
per-problem codebooks. Keep input and storage tradeoffs separate. These measures
can improve without proving human learnability or autonomous solving.

M1–M6 thresholds, historical goal IDs, corpus-admission ownership and protected
boundaries remain unchanged. Legacy 3b reservations map to current 4b. A goal of solving the whole corpus is a target, not
current coverage. This documentation addition launches no experiment and
publishes no new program or private test data.

## Keep representation boundaries explicit

These are definitions for proposed comparisons, not additional implemented arms:

- **AST-selected fixed snippets:** if the decoder still concatenates exact stored
  strings, the representation remains a flat string dictionary. Our existing AST
  preprocessing is in this category; a structured language has different charged semantics under current 2c.
  The local balanced-statement pilot is tracked in the current scorecard; it
  does not turn this historical preprocessing into a structured-language result.
- **Identical whole-subtree reuse:** representing shared subtree identity as graph
  nodes is DAG compression. It changes the representation and must charge its
  structural encoding rather than inherit literal bit costs.
- **Tree patterns with holes:** filling those holes introduces parameterized or
  tree-grammar abstraction. Binding and substitution costs must be explicit; it
  cannot silently count as literal concatenation.
- **Fixed functional code:** a literal may contain `function countValues(values)`
  and a literal call may supply runtime arguments. Runtime function application
  is ordinary JavaScript, not source-template substitution. A general functional
  composition experiment remains planned; existing `map`/`reduce` examples alone
  do not establish one.

No new implementation, benchmark, source rewrite or synthesis run is authorized
by this note. Compare any future proposal against the preserved literal and
whole-program baselines with matched interfaces, evidence and counted storage.

## What the implementation history now supports

The [80-problem measured-gain experiment](scale-v2/README.md) improves actual
dictionary selection and source normalization. Its selectors use exact
counterfactual parsing costs, reclaim redundant learned strings, and measure
bounded remove/add replacements. This aligns with established optimal-parsing
and heuristic-table-learning ideas (OptFSST); it does not establish a new
compression algorithm or a comparison against that implementation.

The distinction from babble/Stitch remains substantive: Gamma presently learns
flat strings, not parameterized reusable functions modulo an equational theory.
Its guarded JavaScript rewrites are not equality saturation. DreamCoder's
library-and-solver learning loop is also not implemented by these experiments.

What is new *within Gamma* is measured evidence: the larger 80-problem development
set, the matched selection/refactoring ablations, counterfactual decision traces,
and a class-binding failure caught and fixed by broader execution. The eight-bit
winner still emits53.2% of its selections as single characters. That finding
limits an algorithm-library claim even while input cost improves.

The research question remains whether jointly rewritten, genuinely reusable
pieces reduce complete input cost on new semantic tasks and can be selected
correctly with little effort. Neither compression, ASCII expressibility nor
finite execution tests establishes that result. No literature novelty claim or
publication-level superiority is supported by the current measurements.

## 2026-10-21 addition: matched optimization and research loop

The preceding 80-problem discussion is historical evidence, not the current
inventory. The latest completed 150-JavaScript and 25-Python aggregate receipts and
full limits are indexed in [research-loop-v1/RESULTS.md](research-loop-v1/RESULTS.md). They remain
separate exposed development populations; neither meets M1 or establishes
an autonomous composer. Original sources, failed candidates and the
79/140-literal baselines remain preserved.

[Tempus et al., ConvexTok: Tokenisation via Convex Relaxations, v1](https://arxiv.org/html/2605.22821v1)
is a central fixed-source vocabulary-selection comparator: shared token
activation couples occurrence-edge paths under a vocabulary budget. LP
relaxation gives a bound and rounding yields a dictionary for exact parsing.
Its reported results do not transfer to Gamma's source rewriting or full packet
costs. The [matched baseline protocol](BASELINE_PROTOCOL.md) pins the restricted
adaptation, cost extensions, candidate fairness and bounded solver tests; the completed restricted diagnostic is reported in
[RESULTS.md](research-loop-v1/RESULTS.md), separately from the broader protocol.

[Casel et al.](https://link.springer.com/article/10.1007/s00224-020-10013-w)
remains the grammar-cost reference. Its acyclic one-level grammar model and
specific size measures must not be treated as a theorem for arbitrary
multi-program literal packets or cyclic expansion. Parameterized/recursive
grammars are separate representations with explicit costs.

The [feedback loop](RESEARCH_LOOP.md) records the owner's dynamic-programming,
source-graph rewriting/reduction, self-referential compression and ring
all-reduce hypotheses. Only exact fixed-dictionary DP and the receipt-backed
source/dictionary experiments are implemented here. Ring all-reduce is a
coordination hypothesis, not a compression result; recursive dictionary
expansion requires a separately specified decoder. M6 is a proposed gate for
publication-worthy novel discovery, not a novelty claim or publication action.
