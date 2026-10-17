# Solver mode boundary

The editor integration is being prepared in Gamma, not deployed to 256.one.
Binary ASCII and JavaScript Huffman are input encodings. Retrieval is a separate
problem-solving mode: the user supplies a problem and examples, inspects a
candidate and explicitly chooses whether to insert it. A retrieval score must
never silently insert or execute code as the user types.

## Current interface

From `projects/algorithm_solver`, on the provisioned Linux judge host:

```sh
../../.venv_rocm/bin/python -m algsolve.answer query.json --index research
```

The default is retrieval only. `--fallback codex` explicitly enables the existing
subscription CLI when a stored answer cannot be verified. It uses the retrieved
candidate as context and the existing generation/repair budget. No Claude,
installation, download or API provisioning happens here.

`query.json` is a normalized `Problem`, including `uid`, `source`, `source_id`,
`title`, `slug`, `statement`, `io_mode`, `entry`, `starter_code`, and parsed
`public_tests`. Example:

```json
{
  "uid": "user:example", "source": "user", "source_id": "example",
  "title": "Sum", "slug": "", "statement": "Return the sum of the integers.",
  "io_mode": "functional",
  "entry": {"class": "Solution", "method": "solve"},
  "starter_code": "class Solution:\n    def solve(self, nums): pass\n",
  "public_tests": [{"args": [[2, 3]], "expected": 5}]
}
```

Expected values remain in the trusted host judge. They never enter the candidate
sandbox. Missing examples, failed examples or a missing sandbox do not produce
an approved answer. No hidden-test file is loaded by the answer route.

The JSON result distinguishes `decision`, `code`, `route`, `example_passed`,
`independent_tests_passed` (null: not evaluated for this query), attempts, time,
ranking and source attribution. `stored_reference_validated` describes the
original reference; it does not establish correctness for an adapted query.
Results retain the label **prior model exposure unknown**.

An injected reranker must return one finite score per retrieved candidate and
have separate development-fitted thresholds. Existing embedding thresholds
cannot be reused for reranker scores. This injection point is implemented;
The `DopplerReranker` adapter has passed a synthetic pair on the existing local F16 model. Algorithm-sibling quality and development-set calibration remain unqualified.

## Index separation

`research` uses the frozen exclusion rules. `--index corpus` explicitly opens the
separate existing all-corpus service index; it is for known-problem lookup, never
for measuring held-out solving or mining components. Corpus self-retrieval
results are not generalization evidence. The original frozen experiments and
vocabulary are unchanged.

## What remains before browser integration

- Parse an editor's actual problem/examples into the normalized request without
  guessing missing assertions or signatures.
- Choose a deliberate local bridge to the Linux sandbox; the static website
  cannot run bubblewrap or trust browser-submitted executable checkers.
- Scope authentication, request sizes, queue limits, cancellation and explicit
  insertion. Do not expose this CLI as an unauthenticated public code runner.
- Qualify paraphrase/sibling recognition and the optional reranker, then show
  match provenance, abstentions and public-example evidence in the editor.

No current result establishes a JavaScript solution adapter: the stored corpus
and judge use Python. A future JS editor mode must show Python explicitly or
qualify a separate JavaScript implementation.
