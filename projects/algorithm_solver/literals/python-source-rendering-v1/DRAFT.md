# Item 38: Python source rendering and dictionary stack

Status: **design and synthetic implementation only, not execution-frozen**. No private population/source/case contents have been read for this item. The executable contract does not exist. Root and Claude review precede activation and launch.

This extends the item31 Python naming mechanism anchor with bounded source formatting and matched dictionary continuation. It is a source-change question, not item34 optional character slots or item35's fixed-source certificate. Component intent is preserved: explicit authority, independent decoding, complete costs, retained qualification failures, no whole-solution entries or protected data. M1/M2 are unchanged.

## Population and controls

Use exactly item31's36 allowed IDs:27 fit and nine consumed validation. Own-width scope_joint sources/dictionaries at128 and256 entries are mechanism anchors, not ready candidates. Closed Python14, all50 loader, final100 and protected66 are forbidden. No widening if the small panel is uninformative.

Public item31 evidence records validation U actions1420/935 at128/256; R records1420/949. U is the actual own-width scope_joint pair. R retains unchanged original sources and the original baseline dictionary with the same canonical encoder.

| Arm | Sources | Dictionary |
| --- | --- | --- |
| U | unchanged item31 scope_joint | exact own-width scope_joint seed |
| S | deterministic renderer menu | exact U dictionary |
| D | unchanged U sources | two continuation rounds |
| J | same renderer menu as S | two continuation rounds |

Widths have separate verdicts. S/U identifies rendering with fixed dictionary; D/U further dictionary search; J/D rendering at equal search budget; J/S dictionary increment after rendering. Source/proposal choices can differ as consequences of the source factor; budgets, codec, legality, objective and cohort remain matched. No across-width winner.

## Renderer

[render.py](render.py) offers at most six deduplicated alternatives: unchanged original; ast.unparse with original literal spans restored; compact token renderings of original/unparsed text with one- or two-space indentation. Nonsemantic comments/spacing may disappear. No renaming, algebra, helper code or new algorithm.

Changed candidates must parse and compile without execution, have exactly equal ast.dump ignoring location attributes with type_comments=True, preserve every original constant and complete formatted/template-string span, and stay within printable ASCII plus LF. Spans retain quote/escape/numeric spelling, adjacent strings, docstrings, f-string debug labels and nested formatted expressions. UTF-8 AST columns are converted correctly even if unparse temporarily emits Unicode from an ASCII escape. The final candidate still must fit the alphabet.

The original is retained. Unsupported means original-only. Whole-source guards reject unknown imports, dynamic evaluation, reflection/source/bytecode/frame/traceback access, exception handlers, suspended frames, decorators/type parameters, class keyword metaprogramming, type comments, string annotations and future-annotations mode. String format/format_map/Formatter are excluded because reflection can live inside a literal. Typing imports/module helpers use a narrow annotation whitelist; evaluating helpers including get_type_hints, ForwardRef, evaluate_forward_ref, _eval_type and _evaluate are excluded. Basic List[int]/Optional[int] remains supported. Bounds:65,536 source bytes,20,000 AST nodes,40,000 compaction tokens.

These conservative guards do not prove Python semantic equivalence. Strict finite qualification remains mandatory after choices seal. Failed selected sources remain failed: no original fallback, second-best rendering, dropped problem, guard tuning or rerun.

## Objective, search and legality

Source choice orders canonical literal selections N, actual packet bytes, source UTF-8 bytes, unchanged-first on an exact cost tie, then lexical source. Fixed-width packet cost depends on N. Normalized original-first/lexical variant IDs therefore match the reused frozen evaluator's (N,source bytes,variant ID). No cases enter the choice.

All96 fallback characters remain. D/J reuse frozen style/joint primitives unchanged: two60-second/12,000-trial rounds, matched neighborhoods, fit-only proposals with the existing shared-owner restriction. Menus remain static. New proposals exclude all full sources and complete Solution entry-method bodies from every fit menu, including unselected variants, identically in D/J.

Audit the **entire actual dictionary, including seed entries**, against all offered fit+validation menu sources/bodies. No inherited exemption. Collisions remain hash-only legality failures that block readiness; covered costs may be descriptive. No post-validation pruning/menu deletion or validation-driven search.

## Sealing, qualification and reporting

Eight fit workers seal dictionaries, fit sources, all menus/variants and search records before any validation-source parse. Eight validation workers make fixed-dictionary choices without search. All eight full source choices and both R references seal globally before any new case read.

Reuse exact passing item31 (problem ID,source hash) only. Qualify each distinct new selected source once across widths/arms. There are288 experimental and72 R views, with at most144 new-source qualifications. Original item31 baseline observations/test hashes remain authoritative. No new descriptions/cases, training or models.

Qualification uses the same oracle, exact JSON type/mutation/alias parity, ordered observations, unique keys, finite JSON and done marker. Each32-case batch uses the pinned sandbox harness,3 CPU/8 wall seconds,512MiB/4MiB output. Exit/timeout/output-overflow receipts and stdout/stderr hashes are retained. Failures remain in denominators, without retries.

The reporter searches/executes nothing. It verifies metadata/source pins, reconstructs deterministic menus, checks AST/literal invariants and correct arm constructors, all seals, canonical source choices, exact independently decoded packets, complete body bans and full costs. Fresh batch observations replay against the exact consumed cases/baselines. Missing/extra arms, choices, jobs or packets cause no-verdict reporting. Qualification/legality failures can have complete reports but block affected comparisons. Coverage failures explicitly label partial encoded-row costs and null full-cohort totals.

Public evidence is metrics, IDs, hashes, fixed enums, counts and booleans. Source/menu/error fragments, dictionary keys, cases and observations remain private. Raw renderer rejection messages are never public.

## Readiness and cost

S/J must pass unchanged strong Python31 gates against **both R and D**, plus strict incremental gates against U. J additionally needs incremental gates versus S for stacking readiness. Each comparison requires both full36 qualified,27/9 coverage, legal dictionaries and own-width entry budgets.

Strong:≥5% fewer validation actions, strictly lower median/p90 actions,≥6/9 better,≤2/9 worse, nonincreasing single-character fraction, raw package≤105%. Incremental: strictly fewer actions, nonhigher median/p90/fraction,≤2 worse, package≤105%, same complete-cohort gates. No partial-cohort/subset/best-width promotion. U/D are controls.

Every split pays the entire serialized shared dictionary once plus all packets,41-byte framing, padding and one Finish per program. Standalone per-program packages pay the whole dictionary again as a separate deployment view. N/actions/source bytes/single-character codes/payload bits/padding are separate. Decoder-inclusive costs add pinned13,010-byte decoder source inventory. Offline implementation bytes and fitting/supervisor wall time are separate; installed Python/standard-library footprint is unmeasured. Model bytes/training compute are zero. Search/qualification cost is not amortized away.

M1 remains400/500,≤256 entries, median≤32/p95≤96 selections,≤10% single-character bits, zero whole-solution entries. This36-problem development panel cannot establish M1 or generalization. M2's non-autoregressive rule is unchanged.

## Development evidence

Thirty-three synthetic tests: renderer semantics/spans, indirect formatting/typing reflection, alphabet, ties, factorial controls, body bans,360-view independent artifact replay, missing-arm/packet tampering, no-verdict failures, seed collisions, strict type parity, output-overflow retention, partial-cost labeling, exact activation matching, runtime drift, finite/bounded timing, metadata allowlists and stale-report replacement. Fixtures are invented source/case data in temporary directories. No corpus numerical result is implied.

Preactivation review amendment, 2026-10-23: activation now compares every current draft field to the reviewed pending contract before changing only execution_authorized. It also verifies bytes behind inherited pins, and explicitly pins the resolved interpreter plus ast.py/tokenize.py. Reporting enforces finite coherent timing receipts and an exact input-metadata allowlist; only fixed search-stop enums can be public. A failed replay replaces both metadata and any previous successful REPORT.md with no-verdict evidence. This draft remains unactivated; no private inputs were read for these changes.
