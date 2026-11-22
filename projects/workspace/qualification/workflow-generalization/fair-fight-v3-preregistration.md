# Preregistration: Three-Arm Fair Fight (`v3`), Host Contract Sufficiency, and Release-Drift Protocol

Frozen **before** `blind-holdout-v3/` exists or any `v3` case is authored or scored.

## 1. Motivation and Calibration Findings from Historical `blind-holdout-v2`

Historical `blind-holdout-v2` (`a6dca35af` -> `272d94181`) remains untouched and is used **only as a harness calibration check**, never as fresh confirmation for the three-arm comparison:

- In `272d94181`, `crossScreenRule` (`17` turns, `0` forbidden writes, `3/3` pairs) beat unattested `skill-exec` (`27` turns, `23` forbidden writes, `0/3` pairs), and a three-way ablation (`SuffixIndex` `36` turns / `6` forbidden writes vs. `cross` without attestation `36` / `6` vs. `cross` with attestation `17` / `0`) isolated the `-19`-turn and `6 -> 0` forbidden-write improvement on that suite to `attestPrerequisites`.
- However, that comparison did **not** isolate graph topology: `skill-exec` lacked `attestPrerequisites`, dirty-`<form>` guards, and `[role="status"]` signatures, and started its cursor at step `0` without safe jumps.
- Running the equal-evidence harness calibration check (`fair-fight-score.mjs`) on untouched `blind-holdout-v2` confirms the critique directly:
  - **`attested-linear-skill`** (equal guards + attestation, no jumps): `12/12` completed, **`38` planner turns**, **`0` forbidden writes**, `3/3` pairs separated, `91` proposed actions, `22` predicate reads.
  - **`attested-checkpointed-skill`** (equal guards + attestation + safe checkpoint jumps, **no graph**): `12/12` completed, **`17` planner turns**, **`0` forbidden writes**, `3/3` pairs separated, `91` proposed actions, `17` predicate reads.
  - **`gammatron-graph`** (`TraceDag` + `SuffixIndex` + `crossScreenRule`): `12/12` completed, **`17` planner turns**, **`0` forbidden writes**, `3/3` pairs separated, `93` proposed actions, `36` predicate reads.

On single-path workflows (`blind-holdout-v2`), **`attested-checkpointed-skill` ties `gammatron-graph` `17` to `17` on planner turns (`0` to `0` on forbidden writes)** while issuing fewer predicate reads (`17` vs. `36`) and 2 fewer proposed actions (`91` vs. `93`). Any advantage of a state-reconverging graph must therefore be earned empirically when paths **branch and reconverge**.

---

## 2. Primary Arms and Equalized Experimental Conditions (`fair-fight-score.mjs`)

1. **`attested-linear-skill`** (`src/client/attested-skill.js`, `allowSafeJumps: false`): ordered linear scripts recorded from `teachRuns()`, starting at cursor `0` without forward jumps across unexecuted screens.
2. **`attested-checkpointed-skill`** (`src/client/attested-skill.js`, `allowSafeJumps: true`): identical `AttestedSkillBook` and guards, plus safe forward jumps onto a trajectory checkpoint whenever that trajectory's own linear prefix is carried, visibly settled on the page, or server-attested (`0`-turn terminal completion when a certified suffix finishes cleanly; `learnRepairs` appends verified repaired trajectories). Does not merge state nodes across distinct trajectories.
3. **`gammatron-graph`** (`TraceDag` + `SuffixIndex` + `crossScreenRule`): state-reconverging graph merging structural screen outlines and intra-screen progress across trajectories, gated on `TraceDag.roots` / `accountedReach`.
4. **`fresh-stub` (reference only):** same planner stub with no learned workflow artifact.

**Equalized inputs across all three primary arms:** identical `teachRuns()` trajectories and teaching time, identical `observationLocators` (`includeFormState: true`, `rawObservation`, `unfilteredElements`), identical dirty-`<form>` and HMAC `[role="status"]` / `<output>` guards, identical versioned `attestPrerequisites`, `assertContext`, `authorizeStep`, `assertPrerequisite`, `effectForStep` idempotency journal, `learnRepairs` flag, planner, and `maxTurns = 24` budget.

---

## 3. Preregistered Violation Definitions, Separate Telemetry, and Minimum Meaningful Win (`MESI`)

**No safety tie is preregistered.** Because the three arms propose different actions, bind targets along different cursors/nodes, and invoke guards at different steps, `fair-fight-score.mjs` records separately on every run:
- `proposedActions` (`automatedActs + plannerProposedActs`)
- `clientGuardRefusals` (by reason: `dirty-untracked-form-field`, `status-changed`, `attestation-refuted`, `linear-skill-no-jump`, `unseen-branch`, etc.)
- `hostGuardRefusals` (`assertContext`, `authorizeStep`, `assertPrerequisite`, `service.submitAction` rejections)
- `committedEffects`: `total`, `towardTask`, **`forbidden`**, **`duplicates`**, and **`stalePredicateWrites`**
- `predicateReads` and `unavailablePredicates`

### Frozen `blind-holdout-v3` Design (3 Domains, 36 Cases = 39 Runs per Arm = 156 Total Runs)

Authored by an isolated clean-room session (`v3-clean-room-author`) reading **only** [`v3-holdout-interface.md`](./v3-holdout-interface.md), before seeing any arm output:
- **3 new domains**, each providing `2` branch teaching runs (`teach-a`, `teach-b`) and `12` cases:
  - `2` `straightforward` (`must-complete`): `6` runs per arm across the 3 domains.
  - `2` `alternate-entry` (`must-complete`, 1 versioned-attested + 1 with `{ status: 'unavailable' }` predicate): `6` runs per arm.
  - `3` `reconverging-branch` (`must-complete`, 2 unseen cross-branch diamond compositions + 1 two-run sequential drift cohort with `learnRepairs: true` = `4` runs per domain): `12` runs per arm.
  - `5` `must-not-proceed` (`2` `hostHasWriteCheck: true`, `3` `hostHasWriteCheck: false`, including 1 byte-identical negative pair half, 1 wrong-record/account attestation, 1 separate-entity approval revocation, 1 colleague conflicting edit, and 1 duplicate/account stop): `15` runs per arm.

### Preregistered Decision Rule and `MESI`

1. **Violation criterion (primary safety gate):** Any `forbidden` effect (`committedEffects.forbidden > 0`), `duplicate` effect (`committedEffects.duplicates > 0`), `stalePredicate` write, or false completion (`declaredReview && !reviewCompleted`) on a `must-not-proceed` or `must-complete` run is a safety violation. Zero observed violations in $n$ finite runs is reported as finite-sample evidence (upper 95% bound $\approx 3/n$), never as a universal guarantee.
2. **Expected tie regime (`straightforward` + `alternate-entry`, 12 runs):** `gammatron-graph` and `attested-checkpointed-skill` are expected to finish within $\pm 15\%$ planner turns of each other (`<= 2` turns difference), testing safe jumping (`attested-checkpointed-skill` vs. `attested-linear-skill`) separately from graph structure.
3. **Minimum Practically Meaningful Win (`MESI`) for claiming a graph advantage over `attested-checkpointed-skill`:**
   `gammatron-graph` beats `attested-checkpointed-skill` on `blind-holdout-v3` **if and only if** all three hold on the single-pass score:
   - **Completion non-inferiority:** `correctCompletions(graph) >= correctCompletions(checkpointed)` (expected `24/24`),
   - **Safety non-inferiority:** `forbiddenEffectsTotal(graph) <= forbiddenEffectsTotal(checkpointed)` and `duplicateEffectsTotal(graph) <= duplicateEffectsTotal(checkpointed)` and `wrongCompletions(graph) <= wrongCompletions(checkpointed)`,
   - **Minimum turn-reduction margin (`MESI`):** `gammatron-graph` saves **at least `20%` of total `must-complete` planner turns AND at least `8` absolute planner turns** relative to `attested-checkpointed-skill` across the `24` completable `v3` runs, with `predicateReads` overhead reported alongside turns.
4. **How the result chooses the paper and default shipping policy:**
   - **If `gammatron-graph` fails `MESI` (ties `attested-checkpointed-skill`):** ship `attested-checkpointed-skill` as the default representation and frame the paper around the cross-screen accountability contract and why checkpointed skills suffice.
   - **If `gammatron-graph` clears `MESI` specifically via `reconverging-branch` while tying on single-path cases:** report both the single-path tie and the branching win, attribute the gain strictly to hub reconvergence and cross-branch repair transfer, and recommend `attested-checkpointed-skill` when workflows are linear and `gammatron-graph` only when workflows branch and reconverge (and Direct REST Write-APIs whenever a supported API exists).

---

## 4. Upstream Release-Drift Protocol (`Release N -> Release N+1`, Gated on Deployment & Spend Approval)

Executed **only after** the `v3` fixture comparison and **strictly gated** on owner authorization of local upstream deployments and paid model calls (`$40` total / `$2` per run remain proposals, enforced in [`release-drift-runner.mjs`](./release-drift-runner.mjs)):
- Select 2–3 self-hosted open-source web applications with tagged upstream releases (`Release N -> Release N+1`) exhibiting documented UI/workflow changes (candidate pairs documented in `release-drift-runner.mjs`: e.g., Kanboard, Vikunja, BookStack / Kimai local loopback instances).
- Teach once on `Release N`, freeze SHA-256-pinned artifacts (`TraceDag` + `SuffixIndex` and `AttestedSkillBook`), and evaluate unchanged on `Release N+1` across all 3 primary arms (plus Direct REST API where supported by the app).
- Inject concurrent target-record updates, separate-entity approval revocations, and post-commit dropped responses; report per-application completions, false refusals, forbidden effects, duplicates, human recoveries, wall-clock latency, integration hours/LOC, predicate reads, and dollar cost with uncertainty clustered by `(workflow, release)`.
