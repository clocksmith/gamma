# Gammatron #88: independent offline holdout

**Result:** 21 pairs (42 evaluation rows), three synthetic workflow domains. Both arms completed 9/9 exact reviews and safely refused 12/12 negatives before dispatch. Suffix matching used 18 vs. 42 scripted planner decisions, with 39 vs. 18 cached steps and 3 certified suffix rejoins. The 57.1% difference is in scripted decisions, not measured latency or production model calls.

Exact Gamma source: `5b79bceccf6cc0efbba6a35823d02bb8c77f0233` ([commit](https://github.com/clocksmith/gamma/commit/5b79bceccf6cc0efbba6a35823d02bb8c77f0233)). [DECO #88](https://github.com/clocksmith/deco/issues/88) remains open.

## Files

- `frozen/`: exact protocol, independently authored fixtures, runner, and input checksums from before execution.
- `observed/summary.json`: original row-level and aggregate receipt, including source digests and both arms' permissions, dispatches and outputs.
- `observed/audit.json`: verified comparison of 21 paired recipes and 42 effect journals, with paired case counts and refusal paths. This archive excludes the separate raw journals; a reproduction creates its own.
- `SHA256SUMS`: verifies every included member except itself.

## Reproduce

The runner needs a clean adjacent `gamma/` checkout at the exact pin; it is not a standalone replacement for Gamma. The original ran on Linux with Node.js 22.21.0 and GNU `sha256sum`. It needed no npm install, API keys, hosted tenant, browser, or GPU. Git access to the Gamma source is required for checkout only.

Copy this directory to fresh scratch space, then run the following from the copy. A sparse fetch avoids downloading unrelated Gamma datasets.

```sh
base=$PWD
pin=5b79bceccf6cc0efbba6a35823d02bb8c77f0233
sha256sum -c SHA256SUMS
git init -q gamma
git -C gamma remote add origin https://github.com/clocksmith/gamma.git
git -C gamma sparse-checkout init --cone
git -C gamma sparse-checkout set projects/workspace
git -C gamma fetch --depth=1 --filter=blob:none origin "$pin"
git -C gamma switch --detach FETCH_HEAD
test "$(git -C gamma rev-parse HEAD)" = "$pin"
test ! -e receipt
env -i PATH="$PATH" HOME="$base" GAMMATRON_FIXTURE_ONLY=1 node frozen/run.mjs "$base"
```

Read `receipt/summary.json` in the new run. Compare counts and semantic outcomes, not receipt hashes: generated graph keys, action IDs, and journal details can differ.

## Limitations

The pinned workflow implementation executed against synthetic snapshots and a common in-memory action adapter with durable per-effect fixture journals; it did not exercise real Chromium, authenticated user accounts, production dispatch, network calls, or model APIs. Each arm used the same teaching graph, scripted planner, exact review oracle, resume policy, and prerequisite/tenant guards. The three domains are clustered variants, not 42 independent estimates. The outcome warrants browser and authorized tenant qualification, not closure or broad safety or performance claims.
