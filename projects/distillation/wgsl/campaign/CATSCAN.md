# CATSCAN: WGSL training campaign

Parent: [WGSL distillation](../CATSCAN.md)

## Target

Preserve the WGSL repair and writer campaign, with host-teacher and student code experiments, as replayable evidence executed against an explicit Doppler checkout.

## Authority

- Owns campaign corpus and task construction, frozen policies, harness orchestration, evaluation, selection, finalization, and receipts moved from Doppler.
- Does not own Doppler runtime, the `doppler-gpu/training` library, workload capsules, the Gamma trainer bridge, or large evidence bytes stored in Doppler.

## Scope

- Applies to files under this directory and the generated `.namespace/` execution view.

## Contracts

- Input: A `doppler-gpu` checkout selected by `DOPPLER_ROOT`, plus the [campaign protocol](README.md).
- Output: Test results, tool outputs, and receipts in Doppler repository paths, with a launch line naming the Doppler and Gamma revisions.

## Invariants

- Moved files stay byte-identical; frozen policies and receipts pin their hashes.
- Policy paths remain Doppler repository paths; tools run only inside the namespace view.
- Git identity recorded by tools is Doppler's, never Gamma's.
- Large binaries are referenced by Doppler path and SHA-256, never copied here.

## Acceptance

- `node run.js --test` matches the Doppler baseline for the moved tests.
- Evidence: [campaign protocol](README.md) and [policy-schema check](tools/check-wgsl-campaign-policy-schemas.js).

## Non-goals

- Starting new training, evaluation, or promotion runs, or treating campaign results as runtime support.

## Freedom

Any mechanism is permitted if it preserves these boundaries and passes the acceptance evidence.
