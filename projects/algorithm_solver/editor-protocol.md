# Solver mode boundary

The 256.one editor connects explicitly to Gamma’s loopback-only research bridge.
Binary ASCII and JavaScript Huffman are input encodings. Retrieval is a separate
problem-solving mode: the user supplies a problem and examples, inspects a
candidate and explicitly chooses whether to insert it. A retrieval score must
never silently insert or execute code as the user types.

## Current interface

From `projects/algorithm_solver`, on the provisioned Linux judge host:

```sh
../../.venv_rocm/bin/python -m algsolve.answer query.json --index research
```

The provisioned Radeon 8060S path is explicit:
`--index corpus --device cuda`. CPU remains the default; there is no automatic
device fallback. The Python API can retain its embedding model across calls;
each CLI process pays cold loading. The frozen GPU answer journey returned
144/150 known answers, all passing independent tests, and abstained on 50/50
controlled-absence cases. Warm answered medians were 154–179 ms; cold embedding
load was separately 3.00 seconds. See `findings/corpus-answer-gpu-v2/` for scope.

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
When `public_tests` is empty, the route can parse explicit `Input`/`Output`
examples from the statement using its restricted literal parser and starter
signature. It accepts JSON booleans/null without changing quoted strings, and
refuses partial recovery if another explicit example cannot be parsed.

The JSON result distinguishes `decision`, `code`, `route`, `example_passed`,
`independent_tests_passed` (null: not evaluated for this query), attempts, time,
ranking and source attribution. `stored_reference_validated` describes the
original reference; it does not establish correctness for an adapted query.
Results retain the label **prior model exposure unknown**.

An injected reranker must return one finite score per retrieved candidate and
have separate development-fitted thresholds. Existing embedding thresholds
cannot be reused for reranker scores. `--rerank-run <directory> --doppler-cli
<path> --reranker-model <directory>` loads a fully bound development calibration
with the corpus/CPU path. The tested head128 configuration completed real queries
but was rejected on development quality and latency (30/50 accepted known queries
versus 49/50 for retrieval; 13.03 s versus 1.23 s median total). It stays optional
for reproducibility, not enabled by default. Sibling identity errors remain open.

## Index separation

`research` uses the frozen exclusion rules. `--index corpus` explicitly opens the
separate existing all-corpus service index; it is for known-problem lookup, never
for measuring held-out solving or mining components. Corpus self-retrieval
results are not generalization evidence. The original frozen experiments and
vocabulary are unchanged.

## Paired editor bridge

Start `python -m algsolve.editor_bridge` from this lane on the provisioned Linux
judge host, then forward loopback port 8875 to the browsing machine if needed:

```sh
ssh -N -L 127.0.0.1:8875:127.0.0.1:8875 user@judge-host
```

Choose Connect Gamma in the editor and click Connect in the local pairing window.
The token stays in memory, never in URLs or browser storage. Host and origin
checks, exact CORS, frame denial, a 128 KiB request cap and one active job bound
this personal research interface. No public listener or unauthenticated runner
is created. Existing data/model installations are reused without downloads.

`challenge` returns attributed statements, generated signature-only starters and
public examples from the known corpus, with original license notices. It returns
neither stored solutions nor hidden tests. This personal view does not establish
rights to republish statements. The static website exports catalog metadata only.
`retrieve` uses the existing CPU known-answer route, with no generation/reranking;
each disposable job pays cold model loading. Do not apply the separate warmed GPU
latency numbers above to this bridge. Missing/failed examples retain abstentions.
The editor shows source, match, Python language and verdict before explicit insertion.

`run` accepts Python or JavaScript source (64 KiB maximum) and at most 20 public
examples. The host reconstructs a restricted functional problem; client checkers,
hidden paths and resource overrides are ignored. Expected values never enter the
sandbox. The JS harness supports named synchronous functions, positional inputs,
arrays/plain JSON, ListNode/TreeNode markers and in-place argument comparison.
Unsupported values, asynchronous functions, absent examples and malformed output
fail closed. It does not claim all LeetCode signatures/design-class APIs work.

Node runs with JIT disabled and a 64 MiB V8 heap inside the existing Linux
namespace. Functional JS jobs get 3 CPU seconds, 8 wall seconds, 1 GiB address
space and 64 KiB per output stream; Python uses its existing qualified judge.
Scratch jobs get 2 CPU/3 wall seconds. The bridge kills a worker after 90 seconds
independently of the browser. Cancellation unwinds the namespace and deletes task
files; a subsequent job can run. Exact request-byte SHA256 binds results to
language, source, problem and operation. Editing the document/problem invalidates
stale displayed verdicts.

## Evidence and limits

`findings/editor-workspace-v1/` records automated binary-input → Linux public
examples → optional explicit insertion for one JavaScript and one Python Two Sum
solution. It is not human effort evidence or arbitrary-problem qualification.
Focused tests cover wrong answers, output limits, CPU timeout, network/filesystem
isolation, unsupported results, active sandbox cancellation and later capacity.
The existing judge/lane tests remain applicable. Source attribution is not an
independent correctness proof. No JS stored-solution adaptation is claimed.

ASCII stays a seven-bit input alphabet. The owner’s final requirement makes the
active Python and JavaScript encodings exactly 256 entries of eight bits each:
128 ASCII, 123 recurring shortcuts and five commands, with no escape payload.
Huffman v1/v2 profiles are retained as historical evidence, not selectable active
encodings. Input encoding, sandbox execution, known retrieval and unfamiliar
composition remain separate mechanisms and evidence classes.
