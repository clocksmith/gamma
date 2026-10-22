# Source-bound statement/block inventory

A bounded **Python-first preparation tool**, not a solver, optimizer, equivalent
program rewriter, qualified vocabulary or human-learnability experiment.
It reuses the reviewed authoring-variant catalog's pinned source/contract identities
and safe source reads. Python's native AST supplies complete statement boundaries.
Existing `algsolve/synth/mine.py` mines function/class structural shapes; this tool
adds small conditional contracts at statement and contiguous-sibling-block scale.
It does not import that miner's research index or alter its protected split.

## Three families

- Counting: dense zero-filled list initialization/increment; separately, empty
  dictionary initialization and default-zero dictionary increment.
- Head-index queue: list/head initialization, one indexed read followed immediately
  by advancing that same head, and append statements tied to such a queue binding.
- Adjacency: independent-bucket construction, single weighted/unweighted arc
  insertion, and consecutive reciprocal weighted/unweighted insertion pairs.

Names alone do not identify a queue or a dense counter. Same-function syntactic
witnesses are required. They do not prove dominance, type or lifetime: an earlier
reassignment, branch, alias, global/nonlocal binding, overloaded operation or
side-effectful expression can invalidate the proposed contract. The tool records
this as an obligation, never as a verified property. A sparse empty-dictionary
initializer is a candidate counting building block, not proof that its caller
uses it for counting.

Each occurrence has exact UTF-8 byte offsets and original literal bytes, source
and problem-contract provenance, function/control context, binding-role proposals,
syntactic reads/writes, unresolved calls, inputs, outputs/effects, preconditions,
dependencies, complexity caveats and remaining qualification obligations.
Syntactic reads/writes are not live-in/live-out analysis; augmented assignment
explicitly reads its old binding. Comments/CRLF/inner whitespace remain in spans.
Leading indentation and bytes between spans are not magically encoded.

## Separate identities, separate tracks

- `literal-v1`: language plus exact source-span bytes. No substitutions.
- `contract-v1`: operation plus its conditional written contract.
- `macro-proposal-v1`: language, contract and structural shape. Constants,
  operators and attribute names are retained. First-occurrence name slots suggest
  alignment only. They are not scope-safe executable equivalence or a proven
  free-parameter list. Nested callables/comprehensions are rejected from matched
  spans because their bindings need a different analysis.
- `occurrence-v1`: source-bound variant, byte span and operation. Unlike a literal
  ID, it changes when that occurrence moves.

These are stable content identities under the same tool/parser protocol, not
assigned 6-bit codes. No dictionary/selection/operand/escape costs are measured
here. Literal reconstruction and parameterized-macro expansion must later account
for every wrapper, name, constant, binding, dependency and control byte/token.
No escape channel or complete-program coverage is claimed.

## Reproduce

Use the reviewed catalog module already in Gamma; the implementation hash is
checked before import. A changed catalog implementation requires explicit review
and a new pin. This tool never loads or executes supplied solution modules.

```sh
python projects/algorithm_solver/literals/block-inventory-v1/inventory.py \
  --manifest /path/to/cleared/assigned-v1/DELIVERY_MANIFEST.json \
  --manifest /path/to/cleared/assigned-v2/DELIVERY_MANIFEST.json \
  --manifest /path/to/cleared/assigned-v3/DELIVERY_MANIFEST.json \
  --catalog-module /path/to/reviewed/algsolve/authoring_variants.py \
  --output /path/to/new/local/run
python -m unittest discover \
  -s projects/algorithm_solver/literals/block-inventory-v1 -p 'test_*.py' -v
```

The output directory must not exist. Its `inventory.json` contains source text
and witness identities: keep it local/ignored, and review privacy separately before
any publication. Supply only explicitly cleared development manifests. The CLI
does not inspect a corpus ledger, hidden tests, held solutions or other files by
searching for inputs. The existing catalog checks assignment, source and contract
hashes and path containment; qualification remains unknown.

## Observed development support

The first local run parsed the same 60 Python authoring variants used by the
preceding source diagnostic, one per problem, all qualification unknown. It found
52 overlapping occurrences across 14 problems, not 52 independent components:

- Counting: 10 occurrences in 5 problems, all dense-list operations.
- Head-index queues: 26 occurrences in 6 problems. Six read/advance blocks have
  different exact literals but one structural proposal shape.
- Adjacency: 16 occurrences in 5 problems; weighted and unweighted contracts remain
  separate. Single arcs overlap reciprocal-pair blocks and cannot be added as
  independent coverage.
- Sparse dictionary initialization/update: zero witnessed occurrences. The rules
  below are covered by synthetic tests only, not presented as cohort evidence.

## Synthetic examples, not new source witnesses

```python
counts = {}
counts[key] = counts.get(key, 0) + 1
```

The first creates a fresh dictionary. The second reads a default-zero count and
updates one key, conditional on a built-in dictionary, nonnegative integer values
and stable side-effect-free key hashing/evaluation. Do not align it to a bounded
dense array without proving the key-domain, missing-key and ordering differences.

```python
item = queue[head]
head += 1
```

Inputs are queue/head; outputs are item/head. Preconditions include a valid index
and distinct queue/head/item bindings. This retains the consumed prefix and may
return an alias, unlike destructive pop-front. Enclosing queue discipline, parallel
queues and termination remain caller obligations.

```python
adjacency[u].append(v)
adjacency[v].append(u)
```

This pair appends both orientations, preserving duplicates and insertion order;
a self-loop appends twice. It is not interchangeable with a set, weighted bucket,
single arc, deduplicating insertion or adjacency matrix. Partial failure has no
rollback. Endpoint and graph-domain assumptions remain unqualified.

## Next evidence, not a claim

Review source-bound roles/types/effects against each problem contract, including
bounded character counting versus arbitrary integer counting, parallel queues,
weighted edges and self-loops. Then independently qualify exact component
implementations and any newly identified whole-program variants through the
supported correctness harness. Only afterward run joint source/vocabulary search,
with stable codebook assignments and complete per-solution versus installation
costs. JavaScript extraction, whole-program composition, semantic equivalence and
human usability are not established by this increment.
