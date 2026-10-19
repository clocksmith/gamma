# Known-problem lookup with approved references

Use [the qualification report](findings/known-lookup-release-v1/README.md) for the
current release decision, library coverage and recognition results. A source
approval catalog is not, by itself, a passed recognition release gate.

Gamma owns lookup and its Linux checking sandbox. The optional editor is
[256.one/labs/two-button/](https://256.one/labs/two-button/). It retrieves a
candidate only when requested and inserts code only after a separate click.
The current output language is Python. ASCII, Python and JavaScript input
encodings remain separate from solving.

## Run on the provisioned judge host

From `gamma/projects/algorithm_solver`, with the existing corpus, embeddings,
dependencies and Linux sandbox installed:

```sh
../../.venv_rocm/bin/python -m algsolve.editor_bridge \
  --approved-library findings/known-lookup-release-v1/approved-library.json
```

If the browser runs on another computer, forward the bridge's loopback port:

```sh
ssh -N -L 127.0.0.1:8875:127.0.0.1:8875 user@judge-host
```

Open the editor, choose Connect Gamma, and confirm the local pairing window.
Select a challenge or apply your complete statement, signature and public
examples. Request a stored solution, inspect the matched identity and evidence,
then choose Insert if appropriate. Editing the problem invalidates an earlier
answer. Cancellation releases the running job.

For a JSON request using the [existing Problem format](editor-protocol.md):

```sh
../../.venv_rocm/bin/python -m algsolve.answer query.json --index corpus \
  --approved-library findings/known-lookup-release-v1/approved-library.json
```

There is no generated fallback in this mode. It requires the exact library
membership and approved source hashes. Missing data, changed source, missing
examples, unavailable sandbox, failed examples and unresolved identity produce
an error or abstention, never an approved substitute.

## What an answer establishes

- `source.qualification` binds the stored reference to its original independent
  tests, provenance and approval catalog. Unsupported entries remain candidates
  so excluding one cannot silently redirect a query to an approved sibling.
- `match` records exact statement/interface recognition or calibrated retrieval.
  Close sibling versions can remain unresolved. Examples alone do not establish
  identity.
- `example_passed` describes the caller's public examples. The query's
  `independent_tests_passed` remains null: private evaluation checks are not used
  by the service.
- No automatic insertion occurs. Candidate attribution, approval details and
  public-check failures remain inspectable in the editor.

Exact indexed statements with their interface bypass the encoder. Other requests
use the existing Qwen3 embedding model on CPU, without downloads or reranking.
The Python API can retain its context; bridge jobs remain disposable for bounded
cancellation, so a paraphrase request can pay model startup again. Report those
costs separately from warm request time. This interface does not claim every
LeetCode interface, arbitrary descriptions or unfamiliar composition.

## Reproduce qualification

The report links the frozen source qualification, source approval catalog,
complete gated-path check and independently authored recognition opening.
Their contracts bind code and data hashes. Re-running the existing independent
set is regression work after its first opening, not fresh evidence. Protected
composition tasks and the remaining description queries stay outside this work.

No setup command here installs dependencies, downloads weights, republishes the
corpus or exposes a public execution service. Existing source-license notices
remain attached to personal research views and returned answers.
