# B1 v5 development results

Exploratory. `dev` split only, no locked protocol. Receipts are in
`.work/query-swiglu-fastweight-v5/`; `tally_v5.py` reproduces every count.

## Two adapters were tried; the simple one is the result

- **Fixed** (`top2_*` arms in the receipts): the top two layers, ridge fixed at 0.15. This is
  v4's layout with its defects fixed: the anchor comes from the question format, features are
  scaled by their own spread, background rows are weighted once.
- **Selected** (`v5_*` arms): one layer and one ridge strength chosen per table by leave-one-out
  accuracy. This was the main new idea, and it is worse. See "What did not work".

## Fixed adapter, table removed, against the base model with the table present

64 questions per run. Seeds 1003 and 1004 were run once, after the fixed adapter's code was
final; it was never tuned on them.

| Model | Examples per group | Seed | Base, table present | Fixed adapter, table removed | Wins / losses | Seconds per question, base / adapter |
|---|---:|---:|---:|---:|---:|---:|
| Qwen3.5-0.8B | 3 | 1001 | 35 | 38 | 13 / 10 | 1.01 / 0.37 |
| Qwen3.5-0.8B | 3 | 1003 | 32 | 33 | 10 / 9 | 1.00 / 0.24 |
| Qwen3.5-0.8B | 20 | 1002 | 58 | 59 | 4 / 3 | 5.92 / 0.50 |
| Qwen3.5-0.8B | 20 | 1004 | 52 | 57 | 9 / 4 | 5.67 / 0.21 |
| Qwen3.5-2B | 3 | 1001 | 41 | 46 | 11 / 6 | 2.17 / 0.67 |
| Qwen3.5-2B | 3 | 1003 | 35 | 41 | 12 / 6 | 2.68 / 0.57 |
| Qwen3.5-2B | 20 | 1002 | 59 | 57 | 3 / 5 | 13.47 / 0.54 |
| All seven runs | | | 312 / 448 | 331 / 448 | | |

- The base model with the table removed scores 0 of 448. Guessing one of the four valid codes
  would score 112.
- With the table removed, the fixed adapter is level with or ahead of the base model that has
  the table, in six runs of seven. No single run is significant (smallest exact McNemar p is 0.24).
  The claim the data supports is "not worse", at 3 to 25 times less time per question.
- With the table also present, the fixed adapter scores 343 of 448 against the base model's 312.
  One run reaches p = 0.035 (Qwen3.5-0.8B, seed 1001, 12 wins and 3 losses).
- The fixed adapter emits a valid code in 445 of 448 table-removed answers.
- Adapters are 110 to 200 KB. Compile times in the receipts (4 to 63 s per table) include
  capturing sixteen layers for the selected adapter; the fixed adapter needs two.

## What did not work

- **Per-table selection of layer and ridge.** With the table removed, the selected adapter
  scores 280 of 448, below the fixed adapter (331) and the base model with the table (312).
  When the leave-one-out check picks a layer below the last one, the first token is usually
  right but the stop signal fails and the answer runs on ("omega. omega"). The write-strength
  check only looked at the first token. Breaking ties toward a stronger ridge (commit
  `8d3272084`) made it worse on fresh seeds, not better.
- **Reading middle layers.** At the token where the answer begins, leave-one-out accuracy is at
  chance through the middle of the model and rises only in the last three or four layers.
- **Small models with three examples.** With three examples per group the base model itself is
  only at 50 to 64 percent, so there is little to retain.

## Limits

- Development tasks written by the same session that wrote the compiler; two models from one
  family; 64 questions per run.
- A cached copy of the prompt would give the base model's with-table accuracy at about the
  table-removed time. That comparison is not run. The adapter's case against it is size and
  freed context.
- Seeds 1001 and 1002 were looked at while the selected adapter was being changed. The fixed
  adapter's code did not change between any of the runs.

## Runs with same-prompt baselines (2026-11-18, fresh seeds, fixed adapter compiled alone)

64 questions per run. Arms with the table present unless marked.

| Model | Examples per group | Seed | Base | Fixed adapter | Nearest-neighbour cache | Context-aware decoding | Fixed adapter, table removed |
|---|---:|---:|---:|---:|---:|---:|---:|
| Qwen3.5-0.8B | 3 | 1005 | 37 | 41 | 43 | 38 | 34 |
| Qwen3.5-2B | 3 | 1005 | 46 | 47 | 46 | 44 | 40 |
| Qwen3.5-0.8B | 20 | 1006 | 59 | 62 | 59 | 57 | 55 |
| Total | | | 142 | 150 | 148 | 139 | 129 |

- With the table present the fixed adapter is ahead of the base model in all three runs, by 1 to 4
  questions; no run is significant, and a nearest-neighbour cache over the table's own answers is
  about level with it (148 against 150). On this evidence the adapter has no clear examples-present
  advantage over that cache.
- With the table removed the fixed adapter trails the base model with the table in all three of
  these runs (129 against 142), which is weaker than the earlier seven runs (331 against 312).
- Compiling the fixed adapter alone took 2.1 to 2.6 s per 12-line table on Qwen3.5-0.8B.

## Table-level reanalysis by the new B1 owner (2026-11-18, no new run)

`power_v5.py` over all ten development receipts. The unit is the support table and the number is the
difference in accuracy between two arms on that table.

| Comparison | Tables | Mean difference | Better / worse / equal | Sign-flip p |
|---|---:|---:|---:|---:|
| Fixed adapter against base, table present | 64 | +6.3 points | 35 / 9 / 20 | 0.007 |
| Fixed adapter against nearest-neighbour cache, table present | 20 | +0.3 points | 5 / 4 / 11 | 1.0 |
| Nearest-neighbour cache against base, table present | 20 | +3.8 points | 10 / 2 / 8 | 0.29 |
| Fixed adapter, table removed, against base with the table | 64 | +1.2 points | 26 / 22 / 16 | 0.68 |

- With the table present the adapter is ahead of the base model at the table level. That is development
  data: some seeds were seen while code changed, and the three runs made afterwards show +4.1 points over
  20 tables (p 0.45).
- It is not ahead of the nearest-neighbour cache. Both are a vote from the table's own examples added at
  the output, so there is no mechanism by which the adapter should beat the cache with the table present,
  and the data shows none. An examples-present claim of "better than a cache" is not supported.
- With the table removed the adapter is level with the base model that has the table over all runs, and
  6.9 points behind in the three later runs. "Not worse" is unproven; the draft now requires a
  non-inferiority test for it.
- Power: at the development effect, 48 tables per model pass the primary gate about 68% of the time and
  96 tables about 91%. The draft protocol now asks for 96.

What the adapter can offer that a cache over the prompt cannot is the table removed: 110 to 200 KB in
place of the table's tokens, and no limit from the context window. The claim with a mechanism behind it is
therefore "table removed, not worse than the base model reading the table", tested against a cached prompt
on size and time, and "more examples than fit in the prompt", which no arm here tests yet.

## Zero-GPU audit (2026-11-19, no new run)

`audit_v5.py` over the same ten development receipts, run on a CPU host. It regenerates each receipt's
tables from `tasks_v5.py` and checks every expected answer against the receipt.

**What the misses are.** With the table removed the fixed adapter missed 180 of 640 questions: 176 answered
with a different valid code from the same table, 3 started the right code and drifted, 1 was not a code,
and none were empty or stopped early or late. The base model reading the table misses the same way (183 of
186). Multi-token codes are not the problem: 238 of 320 against 239 of 320 for the base model with the
table. Teaching every answer token plus the stop token would address 3 misses in 180.

**A favourite code.** In a balanced table each code is the right answer a quarter of the time, so always
answering one code scores exactly 25%; the adapter's 331 of 448 with the table removed (74%) is far above
that, and the skew below is a bias inside real retrieval, not the source of the score. The most
frequent answer takes 47% of a table's answers for the base model with the table, 49% for the adapter with
the table removed and 49% for the adapter with the table. 76% of the adapter's table-removed errors are its
favourite. With the table removed that favourite is often the word `alpha` (42 more `alpha` answers than
there were `alpha` questions); with the table present the adapter's favourite is the code of the last
support line in 30 of 64 tables, against about 16 by chance. The `alpha` pull does not cost accuracy
overall: on tables that use `alpha` the adapter scores 87 of 144 against 85 for the base model with the
table.

**The 6.9-point drop in the last three runs.** By run group, adapter with the table removed minus base model
with the table:

| Seeds | Tables | Difference | Standard error | Runner | Compiler |
|---|---:|---:|---:|---|---|
| 1001-1002 | 24 | +3.9 | 3.8 | `1b252eaf9` | `1b252eaf9` |
| 1003-1004 | 20 | +5.9 | 4.6 | `1b252eaf9` | `8d3272084` |
| 1005-1006 | 20 | -6.9 | 4.4 | `2c7c83566` | `8d3272084` |

The runner change between the last two groups does not touch how the fixed adapter is built: the same
`fitLayer` calls with the same ridge, write strength and rows. It only stops capturing the layers that the
dropped per-table selected adapter needed. The receipts do not record which Doppler they ran on (the runner
now does). Corrected 2026-11-19: the Doppler worktree the runs were launched from has sat at `e45824b09`
with a clean `src` since 2026-11-17 17:14 EST by its reflog, and the first of the ten receipts was written
at 22:27 that evening. A change in Doppler's source is therefore excluded unless a run was pointed at
another checkout, which the old receipts cannot show. Other run conditions (GPU load, memory pressure) were
not recorded. The base model with the table scored 70.3% in the last group against 58.1% in the one before,
so those tables were easier for it, and most of the drop is on two-part codes (66 of 96 against 75 of 96).
Read: no cause found in the runner, the compiler or Doppler's source; table-to-table variation is the
leading explanation. Re-running seed 1003 on that worktree with the current runner would confirm it, as a
diagnostic outside confirmation.

**Size and compile time, corrected.** The 110 to 200 KB quoted above is the single-layer selected adapter.
The fixed two-layer adapter that every comparison uses is 221 to 405 KB on Qwen3.5-0.8B and 393 to 721 KB
on Qwen3.5-2B. It compiles in a median 2.3 s on 0.8B for a 3-example table (about 160 tokens) and 22.6 s for
a 20-example table (about 956 tokens), because it runs one forward pass per support line. Earlier receipts
include the selected adapter's search in their compile time and are not comparable.

**Power for the exact prompt-removed gate** (one-sided sign-flip test at 0.05 on per-table adapter accuracy
minus base-with-table accuracy plus 5 points; 600 simulated confirmations per cell, tables resampled from
development and re-centred on the assumed true difference):

| True difference | 20 examples per group, 48 tables | 96 tables | 3 examples per group, 48 tables | 96 tables |
|---|---:|---:|---:|---:|
| 0 points | 96% | 100% | 46% | 70% |
| -2.5 points | 58% | 80% | 18% | 29% |
| -6.9 points | 1% | 0% | 1% | 1% |

Large tables are where a confirmation can pass at a feasible size: there the adapter ties the base model
exactly in development (89.1% both, table-level spread 9.9 points) and removing the table saves about 930
prompt tokens. Small tables have a spread of 22.4 points and save about 140 tokens. The earlier "91% at 96
tables" was for the examples-present gate, not this one.

**Tables are not independent draws (found 2026-11-19).** Each split in `tasks_v5.py` has eight item groups
of 28 nouns, and every table samples four of the eight. So 96 confirmation tables reuse the same 224 nouns
and at most 70 group combinations. The sign-flip test and the power figures above treat tables as
independent; they therefore say nothing beyond these eight groups, and probably overstate power. Before
lock: add confirmation groups, or run the test and its power calculation with the group combination as the
resampling unit. The 28-noun limit also caps a table at 28 examples per group, questions included.
Addressed the same day; see "Confirmation design and controls" below.

**Cached-prompt arm, written, not run.** `B1_WITH_KV_SNAPSHOT=1` adds `kv_ctx`: the base model's prefix
state for the table (attention KV plus linear-attention recurrent state) is built once with
`prefillKVOnly` and restored per question. It decodes through the same function as every other arm, so its
answers should match `base_ctx`; the receipt records its build time, restore time, time per question and
state bytes beside the adapter's size and compile time. The pipeline's own cache is restored after each
question and the restored copy destroyed.

**Unseen model.** Corrected 2026-11-19; an earlier version said only that `qwen-3-5-4b` is missing from
Doppler's catalog. v5 has run on Qwen 3.5 0.8B and 2B only. The runner refuses models that normalise after
the feed-forward block (`run_v5.mjs` asserts `!postFeedforwardNorm`), which rules out every Gemma. Doppler
has conversion settings for four candidates that pass that check and use SiLU gating: Qwen 3 4B Instruct,
Qwen 3.5 9B, MiniCPM4 0.5B and LFM2.5 1.2B. LFM2.5 has convolution layers, and whether the cached-prompt
snapshot restores their state is unchecked. There is no Qwen 3.5 4B entry. None of the four has weights on
disk here (manifests only), so each needs a download, which is the owner's decision (host, path, revision).
None has been run through this runner, so a smoke test on public examples comes before any held-out run.

## Confirmation design and controls (2026-11-19, CPU only, owner-approved; nothing locked, nothing run on a GPU)

**Wider confirmation groups.** The confirmation split now has 37 item groups of 28 nouns (1,036 nouns; the
original eight plus 29 new ones). No confirmation noun is a development noun, and no noun is used twice.
Tables are no longer drawn at random: they follow a block design of 111 four-group tables in which every pair
of groups meets in exactly one table, so two tables share at most one group and a group sits in at most 12
tables. A 96-table confirmation uses the first 96 of the seeded order (1,827 of its 4,560 table pairs share one
group; none shares two). Development tasks are byte-for-byte unchanged: their hashes are pinned in
`design_check_v5.py`, which also re-checks the nouns and the design. Six nouns in the original eight
confirmation groups share a whole word with a development noun or an answer code (`apple juice`,
`orange juice`, `coffee`, `bell pepper`, `green bean`, `green tea`); they were left as they were.

**Do item groups matter in development?** `design_power_v5.py` regresses products of centred table
differences on the number of groups two tables share. For the tested number (adapter with the table removed
minus base model with the table) the share of table variance that travels with groups is estimated at 0.00
over all 64 tables (5th to 95th percentile -0.37 to 0.42, permutation p 0.46), and negative on the 16
20-example tables. So there is no sign of a group effect in the difference, and the data cannot exclude a
share up to about 0.4. Each arm's own accuracy on 20-example tables does lean on the groups (share about 0.76,
p 0.09 and 0.10); pairing the arms on the same table removes it.

**Is the gate calibrated, and what is its power?** 4,000 simulated 96-table confirmations per cell, 20-example
development tables as the noise pool (16 tables, SD 9.6 points), one-sided sign-flip gate at 0.05 with the
5-point margin. "False pass" is the pass rate when the truth sits exactly on the margin; 5% is correct.

| Group share of table variance | 0 | 0.05 | 0.10 | 0.25 |
|---|---:|---:|---:|---:|
| False pass, claim about tables from these 37 groups | 5.7% | 5.4% | 5.0% | 3.2% |
| False pass, claim about new groups | 5.1% | 8.8% | 11.9% | 19.1% |
| Same, old design (eight groups) | 4.4% | 18.8% | 25.2% | 32.4% |
| False pass, new groups, group-aware test | 4.1% | 5.6% | 6.3% | 6.8% |
| Power at a true difference of 0 | 99.9% | 99.7% | 99.2% | 96.4% |
| Power at -2.5 points | 80.0% | 76.2% | 72.5% | 68.6% |
| Power at -2.5 points, group-aware test | 70.5% | 63.5% | 56.8% | 41.8% |
| 90% paired-bootstrap interval covers the mean for these groups | 89% | 90% | 91% | 93% |
| 90% paired-bootstrap interval covers the truth for new groups | 89% | 81% | 74% | 61% |
| 90% group-aware interval covers the truth for new groups | 93% | 89% | 87% | 86% |

Read:
- With no group effect, which is the development estimate, the frozen sign-flip gate and the bootstrap
  interval are calibrated on the new design, and the earlier 80% power at a 2.5-point deficit stands.
- As a statement about tables built from these 37 groups, the gate stays calibrated whatever the group share.
- As a statement about new groups, it passes too often once groups matter: 12% at a share of 0.10, against
  25% under the old eight-group design. The new design halves the problem and does not remove it.
- The group-aware test (standard error widened by the covariance between tables that share a group, estimated
  from the confirmation tables themselves) holds 4% to 7%, at a cost of about 10 points of power.
- The noise pool is 16 tables. These are planning figures.

Proposed for the protocol, for owner review before lock: the sign-flip gate stays the primary test and its
claim is worded for tables from these 37 groups; the group-aware interval and the group share estimated from
the confirmation tables are always reported; the result is described as holding for new groups only if the
group-aware test also passes.

**Most-frequent-code control (`mfc_bare`).** One code per table, chosen from the support lines alone. Frozen
rule: the most frequent support code; ties go to the code whose first support line comes first. Tables are
balanced, so it scores exactly 25% on every table: checked on development tables and on all 96 tables of a
confirmation draw, in both the Python check and the JavaScript the runner uses.

**Plain classifier control (`probe_bare`).** A ridge classifier in closed form, fitted per table on what the
fixed adapter is fitted on: the top-two-layer MLP activations at each support line's answer marker, in both
captured contexts, labelled with that line's code. Features are centred and scaled per layer, ridge 0.15 as
for the adapter. For each question it reads the same activations from one base-model pass on the
table-removed question and names a code; nothing is decoded. It is never given a query or a query answer, and
it is scored on the same rows as `top2_bare`. Seven CPU tests pass (it learns synthetic labels, falls to chance
when labels are scrambled, and is unchanged by feature rescaling and class renaming). The runner wiring
(`B1_WITH_CONTROLS=1`) passes a syntax check and has not run on a GPU; its one model-dependent step reuses the
capture function the compiler already uses.

Not changed, by the owner's direction: the bias correction and a batched compile stay in development and are
not in this runner.

**Lock shape adopted (owner, 2026-11-19).** The sign-flip gate is the primary test, its claim is worded for
tables built from these 37 groups, and the result is said to hold for new groups only if the group-aware test
also passes. `protocol_v5_draft.json` is rewritten to that shape (still a draft; the earlier gates are kept
in it as superseded). `gate_v5.py` computes the gate from receipts: an exact one-sided sign-flip test with the
5-point margin, a 90% paired-bootstrap interval, the group-aware test and the group share, the controls, and
the cached prompt's token parity. Ten unit tests pass. Run on the development receipts only to check that it
runs: Qwen 0.8B, 12 tables of 20 examples, 171 of 192 against 169 of 192, +1.0 points, interval -3.7 to +5.2,
one-sided p 0.028; Qwen 2B has four such tables, which cannot pass at any outcome (smallest possible p is
0.0625). These are development tables that were looked at while the code changed, not a confirmation.

**Owner confirmations and the diagnostic plan (2026-11-19, before any diagnostic run).** The table-removed
comparison is confirmed as the primary gate. A tie between the adapter and the plain classifier is confirmed to
mean the 90% interval on their difference lying inside -5 to +5 points; a difference that is merely not
significant is not a tie. On the short Mac check the rule is: stop if the classifier matches or beats the
adapter, or if the adapter's upside is capped below 5 points and the cached prompt shows no clear residency
win. `protocol_v5_draft.json` declares the three diagnostic runs and that rule before they are made: a seed
1003 replay, a cached-prompt parity and cost run, and a 48-table table-removed run for the adapter against the
classifier (48 so that the comparison is not underpowered). `B1_SKIP_ARMS` lets the runner leave arms out, and
`replay_compare_v5.py` compares a replay with its original receipt.

**Scope, stated plainly (2026-11-19, still before any diagnostic run).** Every question is about a noun that
is not in the table, so the task is classification by example: place the new noun in one of the table's four
groups and return that group's code. Nothing here tests recall of a stored item. The simple ways to do this
task are therefore the right controls: a plain classifier and a nearest-neighbour vote over the same
activations, and the cached prompt. A nearest-neighbour control with the table removed (`nn_bare`) was added
beside the plain classifier; it reuses the classifier's forward pass. The earlier nearest-neighbour arm
(`knn_ctx`) has the table in the prompt and biases the model's first token, so it is not that control.

**Prior work (recorded 2026-11-19).** FAAST (Bao et al., arXiv 2605.04651, May 2026) compiles labelled
examples into fast weights in closed form with no gradient step at adaptation time and then discards the
examples; it has released code and models. So closed-form compilation is not this study's contribution. What
is left to claim is a systems result, and the plain classifier and nearest-neighbour controls matter more:
FAAST's own few-shot classification tables put its closed-form map, a linear probe and kNN within about 2
points of each other. Differences: FAAST adds a module with a readout that is trained once; v5 writes into an
existing MLP weight with nothing trained. Only the abstract and main text were read, through a summarising
fetch; the method should be read in full, and whether to run it as a baseline decided, before confirmation.

## Diagnostic window and decision (2026-11-19, Mac GPU, development split, declared beforehand)

Three runs, declared in `protocol_v5_draft.json` before they were made, on the Doppler worktree at `e45824b09`
(clean). Development tables only; nothing here is a confirmation. Receipts are beside the earlier ones:
`*_dev1003_k3_replay.json`, `qwen35_08b_dev1101_k20_cache.json`, `qwen35_08b_dev1102_k20_classifier.json`.
`gate_v5.py`, `tally_v5.py` and `replay_compare_v5.py` reproduce every number below.

**A. Seed 1003 replays reproduce exactly.** On Qwen 3.5 0.8B and 2B, every question in the four arms the old
and new receipts share (`base_bare`, `base_ctx`, `top2_bare`, `top2_ctx`) gave the same tokens as on
2026-11-17: 64 of 64 in each arm on each model, with the same counts correct (0.8B: 0, 32, 33, 34; 2B: 0, 35,
41, 43). A seed's outcome is deterministic on this runtime, so the 6.9-point drop in seeds 1005 and 1006 is
those seeds' tables, not a runtime change or noise.

**B. Cached prompt and controls** (0.8B, seed 1101, 4 tables of 20 examples, 64 questions):

| Arm | Correct of 64 | Median ms per question | State kept per table |
|---|---:|---:|---:|
| Base model, table in prompt (`base_ctx`) | 55 | 6,248 | none |
| Cached prompt (`kv_ctx`) | 55 | 246 | 31.4 to 33.3 MB |
| Adapter, table removed (`top2_bare`) | 61 | 250 | 221 to 405 KB |
| Adapter, table in prompt (`top2_ctx`) | 61 | 6,089 | 221 to 405 KB |
| Plain classifier, table removed (`probe_bare`) | 64 | 170 | not measured (see below) |
| Nearest-neighbour vote, table removed (`nn_bare`) | 59 | 170 | not measured |
| Most frequent code (`mfc_bare`) | 16 | 0 | none |
| Wrong-label adapter, table removed (`shuf_bare`) | 1 | 256 | as the adapter |

- The cached prompt gave the same tokens as `base_ctx` on all 64 questions. It restores in 2.3 ms (median),
  answers as fast as the adapter, and builds in 3.9 to 4.3 s against 18.7 to 24.6 s to compile the adapter.
  The adapter has no speed advantage over it.
- The cached prompt's state is about 100 times the adapter's. 20.6 MB of it is the linear-attention layers'
  recurrent state, which does not depend on the table's length; the attention cache adds 10.7 to 12.7 MB.
- The adapter carries the table's labels: compiled from wrong labels it answered with the wrong code it was
  taught on 62 of 64 questions with the table removed (12 of 64 with the table present).
- The most-frequent-code control scored exactly 25% on every table.

**C. Adapter against the plain classifier** (0.8B, seed 1102, 48 tables of 20 examples, 768 questions,
table-removed arms only):

| Arm | Correct of 768 | Word codes (384) | Two-part codes (384) |
|---|---:|---:|---:|
| Plain classifier (`probe_bare`) | 742 (96.6%) | 376 | 366 |
| Nearest-neighbour vote (`nn_bare`) | 702 (91.4%) | 352 | 350 |
| Adapter (`top2_bare`) | 689 (89.7%) | 348 | 341 |
| Most frequent code (`mfc_bare`) | 192 (25.0%) | 96 | 96 |

- Adapter minus classifier, per table: -6.9 points, 90% bootstrap interval -8.9 to -5.1 (group-aware -8.8 to
  -5.0); the adapter was better on 1 table, worse on 29, equal on 18 (exact sign-flip p 3e-8).
- Adapter minus nearest-neighbour vote: -1.7 points, interval -3.7 to +0.3: a tie inside the 5-point margin
  by the bootstrap interval (the group-aware interval, -5.3 to +2.0, reaches just past it).
- The classifier is fitted in a median 132 ms per table against 25.1 s to compile the adapter, answers in a
  median 150 ms against 285 ms, and stored as weights would take about 172 KB on this model (four code rows
  plus a mean and a scale, two layers of 3,584 features, 32-bit), computed, not measured; the runner keeps it
  in a larger form.
- Its leave-one-out accuracy on the support lines averaged 0.97 (lowest table 0.91).

**Decision, by the owner's rule fixed before the run.** The rule: stop if the classifier matches or beats the
adapter. It beats it, by more than the 5-point margin, so this is not a tie either. The practical adapter claim
is closed before any lock: no protocol is locked, no confirmation task is generated, and no unseen model is
downloaded for it.

**The readout result.** On this task (place an unseen noun in one of a table's four groups and return that
group's code, 20 examples per group) what is needed is linearly readable from the frozen model's own
activations at the answer marker. A plain classifier on the top-two-layer MLP activations, fitted in closed
form on the table's examples, was right on 96.6% of table-removed questions; writing the same information
back into the weights so that the model says the code (the adapter) was right on 89.7%, no better than a
nearest-neighbour vote over those activations. In run B the model given the table in its prompt, or its
cached prompt, was right on 55 of 64, below both. Scope: development tables from eight item groups, one model
for run C, one runtime. The adapter keeps one property the readouts lack: the model itself emits the code in
its token stream. Nothing here tested whether that is worth its cost.

Not run, and not needed for the decision: run C on the 2B model, the unseen model, and the confirmation.

## Offline discovery on recorded activations (2026-11-19 evening, owner asked to keep going)

The owner's direction after the decision above: do not stop at the closed claim; find a version that works
and can transfer to Doppler and Reploid. The lead was in the same data: a plain readout of the model's
activations (96.6%) beats the model given the table. This section follows it. Development tables only (seed
1102, the same 48 tables as run C); nothing here is a confirmation.

**Method.** One more GPU run (`B1_DUMP_FEATURES`, receipt `qwen35_08b_dev1102_k20_features.json`) recorded,
for every support line and question, the top-two-layer MLP activations and the final hidden row at every
answer position, with the table removed and with it present through the cached prompt, plus 384 questions
about item groups a table does not contain. `discover_v5.py` then scores methods offline. A write into the
last layer's MLP output is simulated exactly, because only the final norm and the output matrix read it
(`dump_head_v5.mjs` extracts that matrix). Check: the simulated first token gave the same verdict as the
runtime on 768 of 768 questions with the table present and 768 of 768 with it removed. Outputs are in
`.work/query-swiglu-fastweight-v5/discover-20261119/`.

**Accuracy on the same 768 questions.**

| Method | Table in the prompt | Correct | |
|---|---|---:|---:|
| Readout (ridge classifier, both layers) | no | 742 | 96.6% |
| Readout, last layer only | no | 741 | 96.5% |
| Last-layer adapter fitted in logit space, with the cached prompt | yes | 743 | 96.7% |
| **Last-layer adapter compiled from the readout (simulated)** | no | **725** | **94.4%** |
| The same, taught to stay quiet at other positions | no | 712 | 92.7% |
| The adapter as built (`top2_bare`, actual run) | no | 689 | 89.7% |
| Nearest-neighbour vote | no | 702 | 91.4% |
| In-context answer, batch-calibrated | yes | 694 | 90.4% |
| In-context answer, calibrated on the table's own lines | yes | 686 to 693 | 89.3 to 90.2% |
| In-context answer as the model gives it (`kv_ctx`, actual run) | yes | 673 | 87.6% |
| In-context answer constrained to the table's codes | yes | 673 | 87.6% |

Paired per table (48 tables, 90% bootstrap interval, exact sign-flip p):
- new adapter minus in-context: +6.8 points (+4.4 to +9.1), better on 30 tables, worse on 8, p 2.4e-5;
- new adapter minus calibrated in-context: +4.0 points (+2.2 to +5.9), p 0.0017;
- new adapter minus readout: -2.2 points (-3.4 to -1.0), p 0.006: lower, and inside the 5-point margin;
- readout minus in-context: +9.0 points (+6.9 to +11.2), better on 34 tables, worse on 2;
- calibrated in-context minus in-context: +2.7 points (+0.7 to +4.8). Calibration recovers under a third of
  the readout's lead, so that lead is not only label bias in decoding.

**The new adapter design.** One layer (the last), rank equal to the number of distinct answer tokens plus
the line break (5 for word codes, 10 for two-part codes; 92 KB and 184 KB as 32-bit floats). It is the
readout written into the weight: a ridge fit from the last layer's MLP activations at every answer position
to one-against-the-rest targets over the next token, features centred and scaled, the centring folded in
through a direction that reads 1.00 (SD 0.01) at answer positions because an adapter has no bias input, and
a write along each token's own output direction at a gain of one median hidden RMS. Gains from 0.5 to 2.0
all give 93.9 to 94.5%. Two-part codes lose nothing: every later token and the line break were right
whenever the first token was (answers fed in for later positions). What separated it from the adapter as
built: one layer, not two fitted independently; centred features; one-against-the-rest targets, with no
separate suppression and stop columns; no background rows.

**Fewer examples.** The readout with 3 examples per code matches the model with 20 per code in its prompt
(87.8% against 87.6%); 5 give 91.7%, 10 give 95.2%, 20 give 96.6%.

**What does not work.** A readout trained only on the single in-context pass does not transfer to
table-removed questions (44%), so the per-line passes are needed (they can be batched). Asking the write to
stay quiet at non-answer positions costs 1.8 points. The logit-space fit is poor with the table removed
(88.8% at best) and best with it present.

**Knowing when a table does not cover a question.** Given the table, the model answered all 384 uncovered
questions with one of the table's codes. Ranking covered above uncovered questions (AUROC, 0.5 is chance):
readout top score 0.91 with the table removed and 0.89 with it present; nearest support line 0.85 (table
present); the decoder's top-code probability 0.80; its margin between its two best codes 0.76.

**Answer directly or look it up** (`lookup_gate_v5.py`; per 100 questions, two covered to one uncovered;
threshold fitted on half the tables, scored on the other half, both ways round):

| Policy, at about 35 lookups per 100 | Wrong direct answers | Unnecessary lookups |
|---|---:|---:|
| Readout score, table removed | 7.2 | 6.8 |
| Readout score, table present | 8.0 | 8.0 |
| Decoder's top-code probability | 14.9 | 7.9 |
| Decoder's margin | 16.1 | 9.6 |
| Nearest support line | 18.1 | 13.5 |
| Never look up | 41.6 | 0 |
| Always look up | 0 | 64.4 |

At 40 lookups per 100 the readout gives 5.4 wrong direct answers against the decoder's 11.9; at 50, 2.3 against
7.7. With the uncovered item groups held out as well, the order is the same (2.4 against 8.1 at 35 lookups).

**Limits.** The adapter numbers are a simulation, exact for a last-layer write and checked against the
runtime on the unmodified model, but not yet run through the runtime with the adapter applied; later answer
tokens were scored with the true answer fed in. The gain was chosen on these tables. One model. Development
tables from eight item groups. The readout still beats the adapter; the adapter's case is that it is an
ordinary adapter (Reploid requests can already select a prepared one) and that the model itself emits the
answer. Next: port the design to the runner and validate it through the runtime on fresh tables.

## Validation of the readout adapter through the runtime (2026-11-19 night, fresh tables, declared beforehand)

The run and its pass rule were written into `protocol_v5_draft.json` before it was made: seed 1103, 48 tables of
20 examples, 768 questions, Qwen 3.5 0.8B on the Mac GPU, Doppler `e45824b09` clean; the adapter is
`readout_adapter_v5.mjs` exactly as chosen offline on seed 1102 (last layer, gain 1.0, ridge 0.15). Development
split, not a confirmation. Receipt `qwen35_08b_dev1103_k20_readout_adapter.json`.

| Arm | Table in the prompt | Correct of 768 | |
|---|---|---:|---:|
| Readout (`probe_bare`) | no | 747 | 97.3% |
| Readout adapter on the cached prompt (`ra_kv`) | yes | 743 | 96.7% |
| **Readout adapter (`ra_bare`)** | no | **739** | **96.2%** |
| Adapter as built (`top2_bare`) | no | 716 | 93.2% |
| Nearest-neighbour vote (`nn_bare`) | no | 708 | 92.2% |
| Model given the table (`kv_ctx`) | yes | 700 | 91.1% |
| The same, calibrated offline from this run's recordings | yes | 703 to 711 | 91.5 to 92.6% |
| Most frequent code (`mfc_bare`) | no | 192 | 25.0% |

- **Declared primary read: it holds up.** `ra_bare` minus `kv_ctx`: +5.1 points, 90% bootstrap interval +3.3 to
  +6.9, better on 28 tables, worse on 8, equal on 12, exact one-sided sign-flip p 3.2e-5 (rule: p < 0.05). The
  offline prediction was +6.8 points; the model given the table did better on these tables (91.1%) than on
  seed 1102 (87.6%).
- **Against the calibrated in-context answer** (reported beside the rule, as amended before the run): +4.2
  points over batch calibration (707; interval +2.2 to +6.1, one-sided p 0.0008) and +3.6 over the best
  calibrated variant here (711).
- **Against the readout:** -1.0 point (-2.1 to -0.1): the readout is still ahead, inside the 5-point margin.
- **Against the adapter as built:** +3.0 points (+1.8 to +4.3), p 0.0002.
- **On top of the cached prompt:** `ra_kv` minus `kv_ctx` +5.6 points (+4.0 to +7.2), better on 50 questions and
  worse on 7.
- **The simulator was exact.** Run on this seed's recordings it predicted `ra_bare` right or wrong on 768 of 768
  questions, and `ra_kv` on 768 of 768.
- **Cost.** The adapter is 92 KB (word codes) or 184 KB (two-part codes) against a median 32.4 MB of cached-prompt
  state, about 180 to 350 times smaller. It is fitted in a median 0.87 s after the same per-line passes the old
  adapter needs. Per question it takes 255 ms against 246 ms for the cached prompt.
- **Its errors.** 29 wrong: 24 another valid code, 5 a stray first token (`.**`) that is not a code. No answer
  ran on past the line break.

The readout results repeat on these tables: covered against uncovered questions, AUROC 0.94 for the readout's
top score against 0.81 for the decoder's top-code probability, and the model again answered all 384 uncovered
questions with a code; at about 35 lookups per 100 questions, 5.2 wrong direct answers gating on the readout
against 13.9 gating on the decoder's confidence (39.2 never looking up); the readout with 3 examples per code
scores 88.4%, with 10 scores 95.6%.

**Independent reproduction of the seed-1103 lookup gate.** Replaying the original policy on the saved scores reproduced
its complete report byte for byte. The following counts use its existing 35-lookups-per-100 target. Sort the 48 table
IDs lexicographically, fit the threshold on alternating whole tables, and test it on the other 24. Reverse the halves
so each question is evaluated once. Each calibration half contains 576 scores. Use its 203rd smallest score as the
threshold and accept equality. No held-out score tied a fitted threshold.

| Direct answer and gate | Covered questions accepted | Correct among accepted covered | Uncovered questions accepted | Wrong direct per 100, all questions |
|---|---:|---:|---:|---:|
| Table-removed readout, top score | 678/768 (88.3%) | 673/678 (99.3%) | 55/384 (14.3%) | 5.2 |
| Table-present decoder, top-code probability | 612/768 (79.7%) | 588/612 (96.1%) | 136/384 (35.4%) | 13.9 |
| Table-removed nearest-neighbor vote, closest support score | 565/768 (73.6%) | 531/565 (94.0%) | 176/384 (45.8%) | 18.2 |

For the readout, 31 of 48 tables accepted at least one uncovered question; the worst accepted 3 of 8. A 95% table
bootstrap interval for its uncovered false-accept rate is 10.7–18.0%, vs. 30.2–40.9% for the decoder and 40.6–51.3%
for nearest neighbor. The intervals resample whole tables within their evaluation halves, conditional on the two
fitted thresholds. The observed lookup rates are 36.4%, 35.1% and 35.7%, respectively. Each policy uses its own
direct answerer. The scoring assumes an ideal lookup and measures neither lookup latency nor classifier setup.
The evidence covers one Qwen development distribution with two covered questions for every uncovered one.
The [audit script](lookup_gate_reproduction.py) and [per-table counts and thresholds](lookup_gate_reproduction_1103.json)
use only existing recorded scores and correctness indicators.

**What this establishes, and what it does not.** On two independent sets of 48 development tables, one model
and one runtime, a 92 to 184 KB last-layer adapter compiled in closed form from a table's examples answers
table-removed questions about 5 points more accurately than the model given the table, at the same time per
question and with about 200 times less state than a cached prompt; the plain readout it is compiled from is
about 1 point better still, and its score also tells when a table does not cover a question. Not established:
a second model, tables beyond the eight development item groups (the 37 confirmation groups are untouched),
tasks other than placing an item in one of four groups, and any behaviour beyond one short answer. The 5-token
stray answers and the gain were not retuned on this seed.

## State at handoff (2026-11-18 08:00 EST)

Nothing is locked. `protocol_v5_draft.json` awaits an independent review and the owner's pin of an
unseen model. Not built: the cached-prompt comparison. The owner's priority is A1 to A3; B1 uses
the Mac GPU only when no A lane needs it.

## Batched support compilation on CPU (2026-11-20)

Four fresh development tables used 20 examples per group, 80 support lines per table and 16
questions per table. The local Qwen3-0.6B-NHS backbone ran under stock Hugging Face Qwen3,
FP32, on an Apple M3 CPU with two Torch threads. This checkpoint had appeared in earlier Gamma
studies. Stock Qwen3 ignores its seven additional TTT projection tensors.

| Operation, summed across four tables | Serial | Batch of 8 |
|---|---:|---:|
| Isolated support forward calls | 320 | 40 |
| Isolated capture | 26.30 s | 11.04 s |
| Complete readout compile, including one full-table pass per table and the Node fitter | 32.31 s | 17.14 s |
| Table-removed exact answers | 58/64 | 58/64 |

Every greedy token stream matched across the two paths. The largest relative L2 difference
in the captured activations or the compiled factors was 1.66e-6 or less. The model reading
the table answered 51/64 exactly. Two of the adapter's misses were outside the table's codes
(`whites` and `deltas west`). These counts describe four CPU engineering tables.
The earlier Qwen3.5-0.8B Doppler result remains the development accuracy reference.

The equivalent Doppler change needs separate position, attention-cache and recurrent/convolution
state for each support line. Its current B1 runner resets one generation state per isolated line.
The next runtime measurement needs independent-row prefill on the provisioned Qwen3.5 model,
one available WebGPU device, and paired serial/batch captures, factors, generated tokens and
end-to-end compile times on fresh development tables.

Receipts and individual answers: [seed 1105](batch_capture_cpu_dev1105.json),
[seed 1106](batch_capture_cpu_dev1106.json). The CPU run command is in the [README](README.md).

An existing unit test run during this work also regenerated the previously documented
seed-2000000 confirmation-design fixture in memory for the fixed 25% constant-code control.
Its only output was test status. The test wrote no cases, and the benchmark and model received
only the fresh development inputs in the receipts above.

## First-token decoder control on CPU (2026-11-20)

All five off-code answers in the prior Qwen3.5-0.8B development validation started with token
194805 (`.**`); 24 other errors used valid codes. The new opt-in decoder restricts only its
first token to starts observed in the support lines. It can still emit any continuation.
The same rule is applied to the table-removed adapter and to the base model reading the
table. The adapter weights and unconstrained arms use the existing readout fitter.

On four further development tables from seeds 1107 and 1108, with the local Qwen3-0.6B-NHS
backbone and the CPU setup above, one of the adapter's 64 greedy decodes changed. The original
output was `deltas`. At that position `delta` was the highest-scoring permitted token,
1.303 logits below the unrestricted winner. The restricted decoder emitted `delta` and
a newline, giving the exact expected code. Every other adapter token stream matched its
unrestricted reference. The base model with the table always started with an allowed token.

| Full decoded answer | Ordinary greedy | Restricted first token |
|---|---:|---:|
| Adapter, table removed | 58/64 | 59/64 |
| Base model, table present | 50/64 | 50/64 |
| Off-code answers from adapter | 1 | 0 |

This is one observed recovery on a development checkpoint. A reserved Doppler run on fresh
Qwen3.5-0.8B development tables is needed to test whether the same rule recovers its stray
starts. `ra_first_bare` and `kv_first_ctx` are implemented, exercised in CPU selector tests
and awaiting that runtime measurement. The CPU script executed both full model decodes.

Receipts with every token stream and score gap are available for [seed 1107](first_token_cpu_dev1107.json)
and [seed 1108](first_token_cpu_dev1108.json).

## MiniCPM4 transfer compatibility (development, 2026-11-20)

The unchanged last-layer readout adapter ran on the independently pinned F16 MiniCPM4 0.5B in Doppler on Apple Metal. All 13 weight files matched the SHA-256 values in the pinned artifact manifest. The [contract](minicpm4_confirmation_lock.json) preceded inference. This compatibility check used two development tables and 32 questions. The 96-table confirmation uses a separate split and seed.

| Method | Word codes (16) | Multi-part codes (16) | Total (32) |
| --- | ---: | ---: | ---: |
| Readout adapter, table removed | 14 | 16 | 30 |
| Plain classifier, table removed | 14 | 15 | 29 |
| Nearest neighbour, table removed | 15 | 15 | 30 |
| Warm KV and plain full-table model | 12 | 15 | 27 |
| Most frequent code | 4 | 4 | 8 |

Warm KV reproduced every generated token for all 32 plain full-table answers. The adapter occupied 102,400 bytes on the word table and 204,800 bytes on the multi-part table. Median used KV state was 14,088,192 bytes, with 25,165,824 bytes allocated on each table. The runner did not measure a serialized classifier or its heap residency.

Median full adapter setup was 63.09 s, including shared support preparation and the model passes, versus a median 0.90 s for the fit and device materialization alone. Shared preparation took 40.84 s and 83.54 s on the two tables. Median classifier setup was 62.39 s, and KV snapshot build was 39.03 s. Median per-question times were 392 ms for the adapter, 234 ms for the classifier including feature acquisition, 1,112 ms for the restored prompt, and 43.40 s for fresh full prefill. These timings were collected on a contended host. The small development sample provides a compatibility check; it establishes neither held-out superiority nor portable speed. [Summary](minicpm4_dev1120_summary.json) · [Per-question receipt (gzip)](minicpm4_dev1120.json.gz)
