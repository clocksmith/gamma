# Frozen predecessor replay on dot

The paired alternatives are optional successors, not replacements for the
historically qualified implementations. A domain mismatch in an alternative
cannot remove a frozen problem or invalidate its original by assumption.

`baseline_replay.py` supports the exact 400 permitted development predecessors
(300 fit plus the previously consumed 100 development-validation problems).
The final held-out 100 and protected 66 remain closed. The 500-problem M1
denominator and every compactness threshold remain unchanged.

## Evidence contract

- Derive the source/case/baseline allowlist from the pinned transfer contracts.
  Verify the transfer receipt, filtered metadata and each selected payload digest.
- Reuse the byte-identical admission harnesses and `qualify_rules.py`, checked
  against their historical contract hashes. List/tree markers and exact-integer
  transport retain their existing behavior; only problem 633 always tags integers.
- Run each original `solve` source through the approved pinned Node adapter.
  Cases enter the isolated task without expected values or historical outputs.
- Require both the original host return oracle and exact historical observation
  parity: result, result type, arguments before/after, alias edges and errors.
- Retain stdout/stderr, failures and their hashes privately outside the repository.
  Missing cases, protocol failures and resource failures do not count as passes.
- Keep `m1_qualified: false`. Runtime replay establishes finite source-bound
  correctness/parity evidence, not a complete literal-cost or M1 verdict.

The replay uses 32 cases per process, 3 CPU seconds, 8 wall seconds, 1 GiB address
space and 4 MiB captured output. Its default total replay budget is 1,800 seconds;
input verification and runtime hashing precede that replay timer, so callers must
also bound the complete command. The existing process-group kill/reap behavior
remains unchanged.

## Run and independently verify

On the authorized native dot desktop, with the approved executable and imported
private package already materialized:

```sh
python3 baseline_replay.py --inputs "$PRIVATE_IMPORT" --output "$NEW_PRIVATE_RUN" \
  --node-path "$PINNED_NODE" --max-wall 1800
python3 verify_baseline.py --inputs "$PRIVATE_IMPORT" \
  --report "$NEW_PRIVATE_RUN/report.json"
```

Use a fresh output directory. `--ids` permits an explicitly named smoke subset;
a subset does not satisfy the default full-400 verification gate.

`verify_baseline.py` independently checks input/runtime/code identities, all
execution and observation hashes, complete per-case oracle/parity replay and
aggregate coverage. It does not trust summary pass flags. Fitting must consume
that verified source identity, not merely a passing count or a different source
inventory. Synthetic tests cover forged observations, even when their reported
hashes are updated, duplicate populations and false execution counts.
