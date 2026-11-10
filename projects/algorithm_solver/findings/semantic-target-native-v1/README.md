# Native target-builder integration on Jupiter

The 2026-11-10 transfer's ten patches applied to `5589e95a1` without conflicts.
The resulting tree is `6efdb13e1b3db5b2d71e674f46be3e31a5a6c045`, exactly the
exported tree. The imported series ends at `540ef5582`; patch authorship is
preserved, while the local commit identities differ from the exporting machine.

The unchanged Linux bubblewrap/prlimit judge now executes the new family-first
builder on Jupiter. [Receipt](jupiter-20261110/receipt.json) and retained attempts:

- [Correct length](jupiter-20261110/correct-length/output/summary.json): public,
  independent and declared-bound checks pass; one pair is emitted.
- [Wrong constant](jupiter-20261110/wrong-constant/output/summary.json): the
  public example passes, the independent example fails, and no pair is emitted.
  The declared-bound stage is never reached after the failure.

Both runs use the existing authored unit-test fixture with `judge=None`, which
selects the repository's real sandbox. No judge injection or direct source
execution substitutes for native qualification. Adapter events confirm that
only the development fixture was loaded; excluded identities are synthetic
metadata. The fixture reservation is not an authority union for the real corpus.

This closes the reported environment blocker and verifies the builder's native
accept/reject boundary. It does not reconstruct the old neural comparison,
improve its reported 0/8 result, qualify a real training corpus, train a model,
or open a protected population. The emitted fixture pair is not installed into
a training corpus. Real corpus preparation still requires its reviewed metadata
and existing reservation union, frozen problem/test hashes and teacher adapters;
those inputs were not included in the transfer.

## Focused checks

Jupiter `.venv/bin/python` passed 226 distinct tests across the changed typed
runtime, builder, bridge, diagnostic, direct search, literal codecs, and existing
judge/lane/comparison checks, plus 813 parameterized subtests. The counts combine
153 initial tests, 71 literal-lane tests, and two added native builder tests;
the repeated 23 builder unit tests are not counted twice. No whole-repository
suite, new model campaign or GPU training was run. The Mac separately passed
the transfer's 47-test subset before native verification.

Reproduce the retained integration controls from the repository root on Linux:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  projects/algorithm_solver/findings/semantic-target-native-v1/verify.py \
  --output /tmp/new-semantic-target-native-run
```

The output directory must not exist. The receipt binds the diagnostic and fixture
source bytes, and hashes each retained artifact. Each builder contract also binds
the codec, planner and judge implementation. The recorded Git head is the imported
series; the diagnostic additions were uncommitted during measurement and are
identified by their source hashes. They are committed alongside this evidence.

Component: `gamma.projects.algorithm_solver`. Intent preserved. Boundary effect:
the transferred code and two native regressions are integrated; sandbox policy,
qualification thresholds, existing corpora and running services are unchanged.
