# Mathematical Problem-Set Quality Standard

Status: organizer policy
Version: `MATH-QUALITY-1`

This policy governs every mathematical problem bank, examination draft, rubric,
solution review, and application reduction maintained by the enwiki9 project.
It does not bind a Seal or authorize solver distribution.

## 1. Four separate artifacts

Every candidate examination must separate:

1. The solver-facing problem text.
2. The organizer-only grading rubric.
3. The immutable version and errata ledger.
4. Any private application or transfer reduction.

The public problem must be mathematically complete without the rubric or
application. The rubric may check the public obligations but may not add
theorems. The application may instantiate a theorem but may not alter its
hypotheses or conclusion.

## 2. Independence

Problems advertised as independent must have disjoint local definitions. A
solution to one may not be required by another. Shared notation is limited to
universal conventions stated before the problems, such as the base of a
logarithm.

Application-layer composition does not destroy mathematical independence, but
it must be documented outside the solver-facing file.

## 3. Closed statements

Every requested claim must specify:

- all quantified domains;
- empty, singleton, and zero-dimensional cases;
- exact versus asymptotic conclusions;
- whether a maximum, minimum, supremum, or infimum is intended;
- the representation of any real-valued or infinite object;
- the computational model behind every operation count or lower bound;
- a deterministic tie rule whenever a canonical witness is requested.

Phrases such as "best possible hypotheses", "sharpest bound you can find", or
"efficient construction" are forbidden unless a formal comparison class is
defined.

## 4. Truth and sharpness

Before release, every fixed theorem must survive:

- boundary-case substitution;
- dimension-zero and empty-set checks where meaningful;
- rational-versus-real attainability checks;
- closure checks for every proposed representation;
- a search for a counterexample to each converse;
- a distinction between exact attainment and supremal sharpness.

If a clause is intentionally open, it must say `PROVE OR DISPROVE`. A
counterexample does not complete a fixed theorem that the organizer stated as
true.

## 5. Constructivity

"Construct" means a finite deterministic procedure from the represented input.
If an input contains arbitrary real values, the problem must supply an exact
finite representation and decidable comparison, or weaken the conclusion to a
set-theoretic existence statement.

A finite certificate must define:

- its fields;
- canonical serialization or ordering when uniqueness matters;
- the verifier's input access;
- the exact predicate checked;
- the operation model for any claimed cost.

## 6. Mathematical depth

A championship problem should require at least two of:

- a non-obvious structural characterization;
- a sharp bound with an extremal family;
- a constructive canonical witness;
- an exact converse;
- a stability or perturbation theorem;
- a locally checkable certificate;
- an interaction between two established mathematical areas.

Routine implementation, numerical experimentation, or direct substitution is
not a mathematical solution.

## 7. Provenance

Every version records:

- an immutable version identifier;
- the source-bound commit and SHA-256 when frozen;
- whether solutions predate the specification;
- every semantic erratum;
- whether the artifact is a problem bank, expert-review draft, candidate
  examination, or bound examination.

Known solutions may be republished as a theorem library or training problem
bank, but not represented as an independently precommitted examination.

## 8. Grading

Each independent problem receives one of:

```text
COMPLETE
INCOMPLETE
INCORRECT
NOT_ATTEMPTED
```

`COMPLETE` requires every theorem, construction, edge case, sharpness claim,
and certificate requested by that problem. Partial lemmas do not become a
complete independent solution.

## 9. Application firewall

No mathematical verdict implies compression, runtime, financial, scientific,
or engineering success unless a separately frozen reduction proves that
implication.

For enwiki9 specifically, mathematical completion never changes score credit.
Only exact counted executable evidence may do so.

## 10. Release audit

Before solver distribution, an independent reviewer must answer:

```text
Are all statements true as written?
Are the problems logically independent as advertised?
Are all inputs finitely represented?
Are canonical choices actually canonical?
Are operation claims bound to explicit models?
Are exact and supremal sharpness separated?
Does the rubric add no hidden obligations?
Does the version ledger identify the governing text?
Is every private implication already conditionally proved?
```

Any `NO` keeps the artifact in expert-review status.
