# Research mapping: proposals, not implemented comparisons

[Return to experiment index](INDEX.md). Sources checked 2026-10-20.

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
| Practical bounded fixed-string compression | [Boncz et al., FSST](https://www.vldb.org/pvldb/vol13/p2649-boncz.pdf), [author implementation](https://github.com/cwida/fsst) | FSST maps 1–8-byte strings to byte codes and permits escaped raw bytes. Our literals have no such length cap and no free raw-source escape. A fair comparator must retain and charge those differences. No FSST experiment has run here. |
| Improve parsing under a learned symbol table | [Chehaidar et al., OptFSST](https://arxiv.org/abs/2607.11271v3) | Optimal dynamic-programming encoding given a table is separated from heuristic table learning. That distinction also matters here. This is a proposed comparator, not an implemented result or evidence of identical formats. |
| Give fixed source pieces structural metadata | [ESTree specification](https://github.com/estree/estree), [Yin & Neubig, syntax-driven code generation](https://aclanthology.org/P17-1041/) | AST metadata and syntax-constrained generation are established tools. Metadata must not insert missing source or imply semantic correctness; the neural paper does not establish Gamma's non-autoregressive goal. |
| Compose functional building blocks | [Balog et al., DeepCoder](https://www.microsoft.com/en-us/research/publication/deepcoder-learning-write-programs/) | Learned guidance for program search from input/output examples is a useful comparator. It does not establish that functional JavaScript rewrites use fewer literal selections or preserve execution cost. |

Searching equivalent source variants for a cost objective is also related to
superoptimization in the broad sense. That conceptual relationship does not
establish equivalence of methods, novelty of this combination, or semantic proof
for our JavaScript transformations. Existing outputs are supported by explicit
domain arguments and finite correctness/input-preservation tests.

## Keep representation boundaries explicit

These are definitions for proposed comparisons, not additional implemented arms:

- **AST-selected fixed snippets:** if the decoder still concatenates exact stored
  strings, the representation remains a flat string dictionary. Our existing AST
  preprocessing is in this category; a new AST-backed composition language is
  still only a proposal.
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
