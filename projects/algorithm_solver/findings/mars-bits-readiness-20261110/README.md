# Mars BITS readiness and frozen experiment preparation

This record captures the verified environment state on Mars (`macOS 26.6.2`,
Apple M3, `24 GiB` RAM, `14.04 GiB` available workspace disk at measurement),
the fail-closed Linux sandbox check, the source-free authorized-development
allowlist closure, and the frozen Mars/Jupiter experiment contract prepared from
baseline commit `52ab15e873900f2f9ff8e39292a4b142345f397c`.

- Sealed readiness receipt: [receipt.json](receipt.json)
  (`receipt_sha256`: `401b59b4635e57c2a7d2f447850a76823e7b3b4322034d00fe574db2b89c342f`)
- Verifier: [verify_mars_readiness.py](verify_mars_readiness.py)
- Frozen pilot proposal: [bits_mars_jupiter_pilot_proposal_v1.json](../../contracts/bits_mars_jupiter_pilot_proposal_v1.json)
  (`status`: `prepared_not_authorized_not_started`)
- Allowlist compiler and isolated adapters: [semantic_allowlist.py](../../algsolve/synth/semantic_allowlist.py)
- Planner and target builder: [semantic_target_pipeline.py](../../algsolve/synth/semantic_target_pipeline.py)

## Host split and sandbox boundary

- **Mars (`darwin` / `arm64`)**: prepares and reviews the frozen allowlist,
  boundary union, planner rules, isolated adapter gates, and evaluation contract;
  receives manifests, checkpoints, and aggregate receipts back from Jupiter.
  `algsolve.judge.sandbox.check_available()` fails closed on macOS
  (`SandboxUnavailable: required sandbox tool missing: /usr/bin/bwrap`), and
  `semantic_target_pipeline.build_targets(..., judge=None)` rejects non-Linux
  hosts before creating an output directory. No macOS execution fallback exists.
- **Jupiter (`linux`)**: designated host for unchanged `bwrap`/`prlimit` target
  qualification, `Qwen/Qwen3-Embedding-0.6B` embeddings, and bounded
  non-autoregressive `TypedPredictor` training once Jupiter's live sandbox/GPU
  checks and explicit owner compute/download authorizations are in place.

## Explicit allowlist and transitive exclusion closure

`semantic_allowlist.compile_committed_allowlist_and_boundary()` compiles the
development allowlist and reservation union from seven committed source-free
files (`0` payload files opened):

- `catalogue/PROBLEM_INDEX.jsonl` (`5,144` rows): seeds only
  `previously_authorized_400` (`400` LeetCode rows), verified identical to the
  `300 dev_fit + 100 dev_val` partition in
  `literals/cost-decomposition-v1/contract.json`.
- Excludes all `4,744` non-allowlisted `PROBLEM_INDEX` rows
  (`historical_reserved382`: `382`, `final100_exact_id_reserved`: `100`,
  `known_corpus_nonreserved_pending_independent_review`: `2,472`,
  `unresolved_global_identity_alias_metadata_only`: `727`,
  `outside-4081-freeze`: `15`, `hack2hire-public-preview`: `1,048`).
- Excludes all reservations in `contracts/sample_manifest.json`,
  `contracts/typed_confirmation_v1.json` (`66` pool rows plus `8`
  `development_audit` identities), `contracts/js_corpus_reservations_v1.json`
  (waves `W001` and `W002`), and
  `findings/known-lookup-release-v2/approved-library.json`
  (`protected_composition_alias`).
- Runs transitive connected-component closure across aliases, semantic families,
  `sibling_base(slug)` stems, and `group_id` structural groups. `103` of the
  `400` previously authorized entries touch an excluded or reserved component
  and stay excluded, leaving **`297` self-contained allowlisted entries** and
  **`236` functional non-paid LeetCode candidates (`175` `dev_fit`, `61` `dev_val`)**
  (`allowlist_sha256`: `d29c4495b1cd9c062a31ec7d0dd6a62abdbe47cd8b1864aabd36690aeb7ea034`,
  `boundary_sha256`: `5628ff61a6ecbeba848fad815fbd38b152f3b68edb29e23102de45e29c6c399e`).

## Authorization boundary

Gamma's recorded 2026-11-09 exception in
`literals/macro-fragment-compare-v1/CONTRACT.md` covers resuming only the
macro/fragment literal comparison over `300+100` `KnownSpecService` sources.
Under `gamma/AGENTS.md` (*"Model downloads, remote providers, and compute jobs
require user authority"*), dataset provisioning, encoder weights/embeddings,
isolated teacher inference (`_public_input` only), and `TypedPredictor` training
remain gated on separate owner authorization. Nothing was downloaded or launched
on Mars.

## Verification

Verify the committed receipt, bound source hashes, and deterministic allowlist
closure on Mars or Jupiter from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  projects/algorithm_solver/findings/mars-bits-readiness-20261110/verify_mars_readiness.py --check
```

At measurement on Mars (`.venv/bin/python`, `Python 3.14.2`, `torch 2.10.0`),
19 focused BITS/typed/allowlist/sandbox test modules passed `173` tests (`3`
Linux-only skipped, `977` passing subtests) and the four isolated literal-lane
suites passed `71` tests (`244` distinct passing tests total, `0` failures).

Component: `gamma.projects.algorithm_solver`. Intent preserved. Boundary effect:
adds opt-in `--allowlist` (`excluded_unallowlisted`) and `--recombination-uid`
(`heldout_combination`) planning gates, fail-closed non-Linux native builder
rejection, source-free allowlist compilation, isolated dataset/teacher adapters,
and the frozen pilot contract without altering existing reservations, codecs, or
sandbox qualification rules.
