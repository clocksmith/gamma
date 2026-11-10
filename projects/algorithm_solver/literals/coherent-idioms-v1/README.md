# Coherent exact idioms v1

This bounded admission pipeline replaces arbitrary token windows with complete
loop/function/condition openings, complete accumulator updates, declarations,
returns, calls, construction/collection/binary expressions, exact formatting and
delimiter joins, AST-owned constructor prefixes/suffixes and operation phrases,
full lexical operands of at least two characters, and separately labelled
structural glue. It reuses the existing macro/fragment comparison's Python AST
and Node internal Acorn span readers. No input program is executed or rewritten.
JavaScript and Python remain separate. Every operand, identifier and numeric
constant in an entry is actual text, paid for in stored bytes and selections.

## API

Add this directory to Python's import path and import `coherent`.

- `enumerate_candidates(records, language)` returns candidates, byte provenance,
  literal identities and evidence states. Language is `python` or `javascript`.
- `promote(candidate)` independently checks the supported local primitive envelope.
- `select_table(candidates, language, width)` selects a deterministic shortlist for
  width 6, 7 or 8. With `records=records`, each width independently seeds a
  complementary union of complete reachable-source paths, maximizing greedy
  coverage gain per added entry, then fills unused slots from the ranked pool.
  Without records it explicitly returns a frequency shortlist. Neither mode
  claims global optimality. The default `policy="strict"` excludes
  every stripped singleton and all whitespace-only entries. Optional
  `policy="charged_glue_diagnostic"` admits separately charged structural glue.
- `segment(source, table)` computes exact segmentation or explicit uncovered byte
  intervals. Selection bits are not complete-program bits unless coverage is full.
- `evaluate_tables(records, language, candidates=None)` is **fit-only**: it selects
  all three widths using these records even if candidates were supplied. It reports
  every input program, total denominator, complete count and uncovered bytes.
- `evaluate_fixed_table(records, table)` validates a frozen table and evaluates
  transfer without mining or reselection, using one batched parse. Use this for
  the separately authorized development-validation set after freezing fit tables.
- `validate_table(table)` rejects duplicate IDs/literals, altered mapping hashes,
  mismatched storage accounting, wrong language/width and forbidden singletons.

`records` maps source IDs to objects with `source` and exact UTF-8 `sha256`.
Supply an explicit `problem_id` to support reuse admission; missing identities
remain generated. Different variants of one problem cannot establish reuse.
An optional `qualification` object has `source_sha256`, `receipt_sha256`,
`contract`, and `status: "passed"`. These fields are **caller-bound provenance**,
not verified judge receipts or authority to access a population. The caller must
validate receipts and authorized development membership before supplying inputs.
The companion runner validates the KnownSpecService boundary before providing records. No private source, witness, or dictionary is included here.

Fitting requires at least one source; a frozen audit may report an empty input
set after validating its table, with an explicit zero denominator.
Inputs are capped at 1,024 sources, 256 KiB per source, 8 MiB total, 160-byte
entries, 8,192 proposals per source and 250,000 distinct candidates. Failures raise
rather than silently dropping a source from the denominator. Require a Node
runtime with its internal Acorn dependency, as in the existing span pipeline.

## Evidence states

- **generated**: a grammar-selected exact span with source/hash/byte provenance.
- **promising**: the same coherent span occurs in at least two distinct source
  hashes and at least two explicit problem identities carrying caller-bound receipt identities. Duplicate IDs or repeated
  occurrences in one source cannot satisfy this gate. This is only a shortlist.
- **trusted**: a promising accumulator also passes the separate verifier's exact
  finite local primitive contract. Current contract: two distinct plain local
  names, `+=` or `-=`, integer operands independently ranging from -8 through 8,
  unchanged right operand and sentinel, 289 cases. Runtime, literal, verifier and
  case hashes are retained. Other operators and loops remain untrusted.

Trust does not extend to floating point, overflow boundaries, dynamic coercion,
objects, aliasing, arbitrary integers, enclosing control flow, full-program
qualification, human readability, or unseen autonomous solving. Parse success or
repetition alone never produces trusted status. The verifier executes only a
whitelisted local primitive, never a supplied solution body; its oracle uses
signed unit movement rather than the candidate's compound assignment operator.

## Literal integrity and cost

Whole sources, function/class bodies and functions are excluded, including their
stripped variants contained inside a longer candidate across the supplied
population. Containment must align to lexical boundaries in the containing
source, so a banned body does not spuriously match part of a longer identifier
or text within a string/comment token. Partial identifiers, keywords
and numeric constants are not proposals and cannot be selected mid-token during
segmentation. UTF-8 offsets are exact, including non-BMP text before a span. Python offsets
use physical LF/CRLF rows, not Unicode splitlines boundaries. Unicode separators
inside strings stay on their parser row; bare-CR newline mode fails closed. Every
emitted proposal must have lexical-token-safe and UTF-8-safe endpoints.

Only in the separately named charged-glue diagnostic, structural glue is admitted
and intentionally not called an idiom: exact punctuation tokens
and exact whitespace runs occupy real table entries and are charged. Singleton
selection count, selection bits and selection fraction are reported. The strict
default excludes them, including whitespace-disguised singletons. A lexical
singleton wrapped in whitespace is not glue. There is no character alphabet,
free argument, renaming, source escape, whole-function fallback or hidden lookup.
Uncovered byte ranges remain uncovered; partially represented bytes do not count
as a complete program. Dictionary storage is reported separately. The core segmentation API reports selection costs only. The source-backed runner
below additionally produces the existing LTV1 packet: a 41-byte header containing
width, dictionary identity and selection count, plus payload and padding. It
records complete packet bits, serialized LTD1 dictionary bytes and decoder source
bytes separately. Dictionary transmission/amortization and user interaction costs
are not collapsed into a single total.

The broad grammar-owned pool is a concrete coverage extension, not a complete
language. Comments, decorators, imports, unusual syntax and unshared names can
remain uncovered. Complete-path seeding uses a minimum-selection path per source;
another path could use fewer distinct dictionary entries. The greedy seed is
therefore bounded search, not an optimal-coverage certificate. Source rewriting
or full source qualification still needs the separate existing contracts.

Synthetic four-program cross-product fixtures in each language now reconstruct
4/4 exactly at every 6/7/8-bit budget in strict mode, using zero singleton entries.
This is authored representation evidence, not a real-corpus coverage result.
Source-backed runs use fit-only dictionary selection and frozen mapping transfer.
New source transformations or semantic programs still require per-source
qualification under existing receipts and population boundaries.

## Development evidence

Run `python3 -m unittest discover -s projects/algorithm_solver/literals/coherent-idioms-v1 -v`.
Synthetic tests cover both languages, state transitions, duplicate-owner rejection,
hash mismatches, whole-body exclusion, partial-token denial, exact Unicode spans,
loop colon/comment edge cases, broad full-program reconstruction, all widths,
full primitive reconstruction and honest
incomplete-program denominators. These checks are not catalogue qualification.

## Source-backed development runner

`run.py` fits only the existing 300 development-fit identities from the pinned
cost-decomposition partition. Each language's tables are sealed before any
100-problem development-validation source is opened. The optional
`--audit-all-authorized` adds a transfer measurement on the existing service's
complete authorized known-source population, without additional fitting or a
fresh-confirmation claim. Missing sources remain in the denominator; each source
open repeats the existing service's protection and receipt gates.

The output must be a new private directory outside Git. It retains exact source
and receipt identities, witnesses, code pins, sealed tables and costs. Selected
spans and every completely represented source are independently reconstructed
from table entries. Complete-program packets are independently decoded using the
existing LTV1/LTD1 codec, with framing and padding charged. Own code, shared shape
and packet readers, and service boundary dependencies are archived and hash-pinned.
These archives and the end-of-run drift check are evidence, not execution
isolation: execute the runner from a separately frozen checkout, keep it unchanged
throughout the run, and retain its manifest. Python and Node versions are recorded. The summary excludes source text and reports actual whole-
program coverage beside conditional cost metrics. Primitive envelope checks do
not qualify new whole programs.

```sh
python3 projects/algorithm_solver/literals/coherent-idioms-v1/run.py \
  --service /absolute/path/to/known-spec-config.json \
  --service-sha256 ACTUAL_TRUSTED_HASH \
  --output /absolute/private/coherent-development-run \
  --audit-all-authorized
```

The wrapper's synthetic tests cover service abstentions, exact hash/receipt
bindings, source-write refusal on mismatch, exact wire framing and dictionary
storage, unknown-versus-zero costs, and unavailable/uncovered denominators.

## Constructor/operand successor

The successor fitting pool adds role-bound `return ` / declaration openings,
function-name openings, call/index/member constructors, condition/loop closings,
assignment/comparison/update phrases, and complete multi-character lexical
operands. Prefixes and suffixes come from AST child boundaries or a named lexer
role within that AST node; they are not arbitrary token windows. A one-character
operand cannot become an entry merely by adding whitespace or punctuation.
It may occur inside an actual operation or constructor phrase (`i++`, `n-1`,
`answer = `, `f(`). Exact formatting and delimiter joins remain fully charged.

New synthetic fitting fixtures vary target names, operand names and numbers so
whole assignment statements do not recur. After freezing an eight-bit table,
both languages reconstruct an authored new RHS combination absent from fitting,
without selecting on that target and without singleton entries. This checks
constructor reuse, not semantic correctness or reserved unseen solving. New
constructor and operand families remain promising only, never trusted from
parsing or recurrence. The original accumulator verifier scope is unchanged.

## Known-source development measurement, 2026-11-10

`development-993-20261110.json` retains the source-free aggregates from a separate
frozen checkout. Fitting used the original 300 development sources per language,
followed by a fixed-table audit of all 993 currently authorized known-source IDs.
This audit includes the fitting IDs; the original 100 exposed validation IDs are
also reported separately. No additional-source fitting or protected reads occurred.

At 6/7/8 bits, exact complete coverage is 4/4/4 of 993 JavaScript sources and
6/8/8 of 993 Python sources, with zero singleton selections. Both languages have
zero complete sources among the 100 exposed validation IDs at every width. These
results do not meet the compactness/coverage goals and are not a solution-quality
improvement claim. The grammar-owned pool makes some complete assemblies possible
without a character escape, but exact names, constants, formatting and unshared
constructs still prevent broad coverage.

The measured wire packets include header and padding. Dictionary bytes and decoder
source bytes are separate; language-runtime installation size, human interaction
cost and a total deployed package were not measured. Native whole-program judge
qualification could not run on this host because bubblewrap cannot create its
NETLINK_ROUTE socket. Its sandbox was neither weakened nor bypassed. Existing
source receipts, exact reconstruction, and finite local primitive checks remain
separate evidence scopes. No milestone status is changed.
