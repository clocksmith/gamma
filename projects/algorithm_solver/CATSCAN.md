# CATSCAN: Algorithm Solver

Parent: [Gamma research projects](../CATSCAN.md)

## Target

Recognize stored solutions; separately learn autonomous non-autoregressive composition of
typed functions, data-structure operations, explicit state and control flow.
Goal 2a assembles known problems; 2b adapts nearby semantic variants. No human
steering or runtime source generation is required. Reusable recipes expand into
those building blocks; a compact neural predictor
selects and connects them, with deterministic assembly and validation. Compare
against search and autoregressive generation. The recorded three-call baseline
does not constrain the composition goal.

The owner-requested human composition goal targets a reusable vocabulary for solving
problems and writing code with minimal total inputs, time to correctness and corrections.
A bounded binary-input candidate uses fixed-width choices with N <= 8 bits per entry;
measure connections, bindings, constants and navigation, not operation labels alone.
The current 43 model labels are not an established optimal human vocabulary.
It covers familiar variants first and unfamiliar combinations separately; the
current three text-entry encodings remain baselines, not dependencies of autonomous
solving. Goal definitions and the
natural-description matching boundary live in [STATUS.md](STATUS.md#matching-and-binary-input-objectives).

## Authority

Owns problem imports, sandbox judging, comparison routes, research answer interfaces, index-only mining, graph datasets, frozen samples and reports. Also owns the user-requested binary-input vocabulary study on permitted reference text; 256one owns its editor UI and runtime packaging. Gamma owns an explicitly paired, loopback-only research bridge to its bounded Linux judge and known-answer interface. No unsupported generalization or benchmark-acceptance claims.

## Scope

`algsolve/`, `contracts/`, `findings/`, `runs/`.

## Contracts

- Input: [run contract](contracts/run_contract.json), [sample manifest](contracts/sample_manifest.json), [composition comparison design](contracts/typed_composer_comparison_v1.json).
- Output: per-item evidence and rebuilt reports.

## Invariants

- Expected outputs never enter the sandbox; verdicts fail closed.
- Held-out problems/aliases stay outside research retrieval, mining and training. The separate all-corpus service index supplies known-problem retrieval only.
- Answers require query-public-example verification; stored validation is not query correctness. Missing sandbox/examples fails closed.
- Goals 1a and 1b share stored-answer recognition. Goal 1b receives one description and returns an answer or abstention with zero follow-up or confirmation questions. Missing distinctions that change the correct answer require abstention; do not invent constraints. Existing assisted-dialogue experiments are historical, not an active 1b route or evidence of one-shot understanding.
- Recognition and composition develop and qualify independently. Composition receives the problem directly, without requiring exact-answer identification or recognition release success. Compare raw and constrained graphs on the same composition cases, measuring executable correctness, validity, abstentions and full correction latency. Protected composition scoring requires a frozen development-qualified composer and agreed baselines; recognition results cannot satisfy that gate.
- Graph proposals cannot bypass vocabulary, binding, resource or execution checks. Preserve raw graphs and explicit correction traces; correction cannot silently substitute a hand-authored solution. Select correction on development data and freeze before protected scoring. Measure useful/harmful corrections and executable correctness as well as validity and full latency; report first-prediction results separately from correction/search.
- Recipes are inspectable expansions, not the primitive vocabulary. Keep bounded-baseline results distinct from finer-grained experiments; learned unfamiliar-composition success requires protected generalization evidence.
- Binary-input studies keep raw references ignored, record pinned sources and measure encoding cost separately from solving correctness and human effort. Public challenge navigation exports metadata only. Paired personal research views may export attributed statements, generated signature-only starters and public examples, with source license notices; never hidden tests or stored solutions through the challenge route. Checked solution retrieval is a separate explicit action.
- Editor jobs require a paired origin/token, bounded requests and execution, cancellation cleanup and exact request/result binding. Python/JavaScript entry alphabets contain exactly 256 eight-bit codes, including commands; ASCII remains 128 seven-bit codes.
- A composable-input experiment must not silently replace those entry alphabets. Count bindings, parameters, navigation and corrections in total input cost; measure complete latency and correctness separately. Nearest-match retrieval does not authorize an exact-problem claim or an unverified adapted solution.
- Training excludes protected families; shared structural patterns and alternative solutions stay together. Tests do not prove correctness.
- Launch the autonomous graph-development loop only after raw composition, constrained composition and protected scoring have independently established receipts. After that gate, a development agent may propose and repair graphs within a recorded compute budget using permitted development evidence only. Retain rejected attempts. Component promotion requires independent contracts/tests and distinct-case reuse; it is not automatic from structural recurrence. Nearby-variant evaluation may share a familiar base while withholding its changed semantics and answer; preserve the existing broader reservation separately.
- Keep the existing family-disjoint confirmation reservation frozen before vocabulary mining. A separately identified nearby-variant test holds changed requirements and solutions out while allowing a familiar base. Structural recurrence does not verify components.
- Generative comparisons share model/budget/repair allowance; repairs see public examples only.
- Separate example-passed, independent-tests-passed and benchmark-judge-accepted evidence.

## Acceptance

[Judge](../../tests/test_algorithm_solver_judge.py) and [lane](../../tests/test_algorithm_solver_lane.py) tests pass before runs.

## Non-goals

Unbounded training, automatic downloads, production editor hosting, automatic insertion, assessment use.

## Freedom

Any implementation preserving these boundaries and acceptance evidence.
