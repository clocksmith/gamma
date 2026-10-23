# Short expression constructors with prefix arity

Board item 5, goal 2c. This is a separate structured representation, not a
flat-literal 2a improvement. Fixed qualified R sources are encoded exactly.
Every constructor, operand literal and nested constructor costs one code of
the same fixed width; one Finish is added per program. No default operand,
identifier binding, name substitution, hidden helper or problem-ID dispatch.

## Hypothesis and population

Structural-v1 charged END for general expression holes. Here a constructor has
fixed arity, and each child is one recursively encoded complete expression.
Its prefix structure supplies the boundaries, avoiding END. A child that cannot
be represented this way does not receive a raw free payload: that constructor
match is unavailable, and ordinary literal encoding covers the source instead.

Use only cost-decomposition-v1's hash-bound R dev-fit 300/dev-val 100 and starting
L-R 128/256 dictionaries. Final held-out 100 and protected 66 stay closed. Existing
validation results informed this design; this is consumed development.

Fit-only pre-freeze audit: 26,099 expression nodes; 32 retained constructor
patterns; 256 retained whole-expression literal proposals; 297 of 300 programs
contain at least one retained constructor pattern. Pattern kinds: 13 member,
14 call, two binary, one update, one logical, one parenthesized expression. This
audit measured support, not candidate dictionary costs. Nine synthetic tests
pass. No corpus constructor search or validation matching has run.

## Encoder, grammar and independent decoder

Acorn with preserveParens identifies expression spans. Candidates are binary,
logical and assignment expressions; unary/update expressions; parentheses;
conditionals; member access; and calls with at most three holes. Holes cover
ordered, nonoverlapping complete AST expressions. Calls expose a receiver/callee
and arguments; the standard Math/Number/String/Array/Object/JSON receivers may
instead be fixed text. Their spelling is stored and charged in the dictionary.

A pattern stores fixed text parts, child AST paths and root fields (node type,
operator, prefix/computed/optional flags where applicable). Total fixed text is
1–32 bytes and less than half the complete program's bytes at each admitted
match. No hole is repeated without another code. No zero-operand constructor.
Types are syntactic expressions, not assertions about numeric/value domains.
Effects and runtime behavior are inherited only through exact source identity.

Pool construction uses fit only: require support in two distinct fit programs,
rank occurrence count times (fixed bytes−1), then canonical pattern text; keep 32.
The parallel pool of up to 256 whole-expression literal strings has lengths 2–64,
two-program support and occurrence×(length−1) ranking. Source/solve-definition/
solve-body strings are excluded from literal proposals.

An expression child is either one literal entry spanning that complete AST
expression or another constructor with its own children. Constructor nesting is
bounded at eight. Body encoding is a minimum-cost path over raw literal edges
and these expression trees. Expression trees use depth-indexed dynamic programming.
All 96 fallback characters remain mandatory, so inability to encode a child
never removes full-program coverage. Ties follow dictionary ID order.

The independent Node decoder parses prefix arity, checks each child is one
complete expression, and reparses each expansion. Root fields and inserted child
boundaries must match the specified AST paths, rejecting precedence changes or
contextual wrappers such as optional chains. The encoder separately admits only
patterns whose standalone expression parse has these same root/child spans.
Malformed/truncated packets, unknown IDs, wrong dictionary hashes, nonzero padding,
truncated operands and wrong child shapes fail closed.

`EXD1` stores every literal and full constructor specification as canonical JSON.
`EXB1` packets use 41-byte framing (magic, width, dictionary hash, count), fixed-width
IDs and zero padding. L uses the unchanged LTD1/canonical packet codec. Both
codebooks contain at most 128 or 256 entries. All constructor metadata, literals,
framing and padding are charged. Raw fixed text is never an external table.

## Four matched arms

At 128/7-bit and 256/8-bit compare literal-only and typed, starting from the same
pinned L-R entries. Both receive the same literal proposal rule: up to 24 contiguous
selected-literal-span merges plus up to 24 fixed whole-expression pool entries.
Only typed additionally receives the 32 constructor candidates. Selected-span
merge proposals can differ after the arms choose different parses; the fixed
whole-expression proposal pool is shared. Literal spans
must be adjacent in source bytes before merging, even inside encoded trees.

Exact evaluation recomputes affected whole-program parses; source variants are
not introduced. In each round, evaluate removing every nonmandatory entry,
shortlist 12 removals by exact selection loss, and evaluate each proposal as an
addition if there is capacity and as a swap against each shortlisted removal.
Accept a strict fit-selection improvement; tie-break by complete package bytes
then dictionary order. Retain the incumbent. No pair moves, random kicks or
learned ranking; this is a bounded neighborhood, not a global optimum.

Per arm: 12,000 exact dictionary evaluations or 600 seconds. Four workers, 4 GiB
address-space ceiling per process, 1,800-second global cap, PYTHONHASHSEED=0.
Report stop reasons and time-limited contrasts. Seal dictionaries and fit pools
before opening validation for each arm. No validation refit or repair.

Every 400-program arm is independently decoded to its pinned source hashes.
Source bytes do not change: reuse existing qualification, with no fresh execution
or unseen correctness claim. Prior 37 judge/lane checks cover unchanged infrastructure.
Nine synthetic codec/cache checks plus compilation/import precede launch.
Commit/push freeze/code/contract and obtain Claude's review before launching,
or record PLAN's 30-minute review timeout if no reply.

## Costs, conditional attribution and predictions

Report fit and validation: coverage, total/median/p90/p95/worst selections and
actions, <=32/96 counts, single-character fraction, constructor entries/codes/
programs, dictionary bytes, packet/framing/padding, package bytes, search trials,
rounds, stop and measured wall time. Finish costs one; navigation/correction and
END costs are zero by this stream grammar, not omitted user actions.

Also report package plus decoder dependencies: typed decoder.cjs and its Acorn
source; literal literals.py and bitpack.py. These are measured source-file sizes,
not complete installed Node/CPython/stdlib footprints, which remain unmeasured.
Keep raw package and decoder-inclusive costs separate; neither is called zero.

Before any dictionary outcome, eligibility is defined as at least one match from
the sealed fit constructor pool. Report typed-vs-literal costs on all 100 validation
IDs, this eligible subset and its complement, with paired better/same/worse
counts. Report actually used constructors separately; do not select only winners.
Global averages do not establish a conditional mechanism's impossibility.

- X1: initial literal parsing reproduces both pinned fit and validation baselines;
  the new literal search may improve them and is reported separately.
- X2: typed 256 lowers validation actions versus searched literal 256, but by <5%.
- X3: typed 128 does not lower validation actions versus searched literal 128.
- X4: all 1,600 packets independently decode and literal whole-solution audits
  are clean; all constructor matches satisfy the fixed-text/operand rules.
- X5: typed decoder-inclusive package cost exceeds literal at both widths.
- X6: no typed arm meets all M1 cost indicators, even on consumed validation.

A typed arm is an **input candidate** for separately proposed confirmation only
if all 100 validation programs decode, audits are clean, actions are at least 5%
below its matched searched literal arm, median and p90 actions are lower, at
least 60 programs improve, at most 25 worsen, single-character fraction does not
increase, and raw dictionary-plus-packet bytes are within 105%. Full decoder/
dependency storage tradeoffs remain explicit even if this input criterion passes;
passing does not establish storage dominance or qualify M1. Choose by actions,
then complete decoder-inclusive package, then width. M1 thresholds are unchanged.

No source/dictionary/sequence publication, BITS deployment, protected opening,
training, learned scorer, human study or autonomous-solving claim. Confirmation
stays at the owner's gate. No ledger/catalog/claim writes.

Component: algorithm_solver literal research, goal 2c. Intent preserved; a new
explicit decoder grammar is isolated from canonical literals and production.
