# Qualified target manifest: BITS step 1 (Track B)

Built on Jupiter (host 128) from source `2acbb6f57` through the repository
sandbox (`verification_authority: repository-sandbox`), using the frozen plan
([plan.json](plan.json), `plan_sha256` c951e1d5…), the reviewed requirements
(`contracts/bits_step1_reviewed_requirements_v1.json`) and the frozen teacher
prompt without recipes (`contracts/bits_step1_teacher_prompt_v1.md`, sha
564bf6df…).

## Teacher

Jupiter's Claude CLI login had expired: `claude -p` exits 1 with "Failed to
authenticate: OAuth session expired and could not be refreshed" in its stdout
JSON envelope and an empty stderr (the teacher now reports the envelope's
error, `6f5cb8712`). As authorized for that case, the frozen Opus 5.5 teacher ran
on Mars (CLI 2.1.322) over the 143 development_fit public inputs not blocked by
review, one call per problem, no retries or feedback. Each record is bound to
the SHA-256 of its exact public input, the plan and the prompt; the Jupiter
build replays a record only when the dataset adapter reproduces that input.
Teacher outputs: sha256 `8da3bea0…` (kept outside the repository with the other
problem-text artifacts).

## Result ([target-build/summary.json](target-build/summary.json), [target-build/contract.json](target-build/contract.json))

| development_fit rows | Count |
|---|---|
| Qualified (public, independent, reviewed boundary and declared probe all passed; training-eligible) | **61** |
| Teacher abstained (representation) | 55 |
| Rejected after a proposal (construction): independent / public / declared probe | 21 / 4 / 2 |
| Blocked by reviewed requirements (lcd:704, lcd:1042) | 2 |

Held out and never opened by the build: 76 heldout_family, 11
heldout_combination; 2 excluded_existing. `pairs.jsonl` (61 pairs, sha256
`9000b57d…`) stays on Jupiter because it contains problem statements.

## Expressibility ([expressibility.json](expressibility.json), from [expressibility.py](expressibility.py))

- **Representation failures:** teacher abstentions by stated reason (keyword
  groups; a reason can fall in several): strings or text 43, trees or linked
  lists 6, nested or 2-D lists 4, division or modulo 1, floats 1, other 1.
  Base-v2 has no string, tree, float or division support; these stay in the
  denominator. Alternative-valid-output contracts (lcd:1042) need a separately
  versioned contract.
- **Construction failures:** 27 proposals the language could express but that
  failed qualification, 21 of them after passing every public example
  (independent tests caught them).
- **Qualified programs (61):** all use `var`/`set` and `for`; 59 branch; maps
  in 36, heaps in 11, queues in 2; no recipe appears (none was offered).

Qualification is finite tests plus reviewed boundary cases, not a proof.
