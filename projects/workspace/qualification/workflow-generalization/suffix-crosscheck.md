# Independent check of suffix eligibility on the frozen generalization experiment

The matcher in `src/client/suffix-eligibility.js` was qualified on its own sandbox
families (see `../gammatron-v4-stage01/README.md`). This runs it through an experiment
written before it existed: the frozen forms, oracle, policy and 13 variants in this
directory. No model is called. `run.js` gains arms and options; nothing frozen changes.

| Arm | Graph | `suffixEligibility` | Resume after planner steps |
| --- | --- | --- | --- |
| `whole` | whole-page | off | off |
| `suffix` | whole-page | on | off |
| `whole-rc` | whole-page | off | on |
| `suffix-rc` | whole-page | on | on |

```sh
node projects/workspace/qualification/workflow-generalization/run.js --controlled \
  --arms whole,suffix,whole-rc,suffix-rc --out bench/out/suffix-crosscheck [--numeric-routes]
```

Other options: `--pair-teaching` (both arm families replay one learned graph),
`--max-cost-usd N` (lower the frozen spend ceiling for a real-planner run), and four
hidden-state variants named with `--variants` (a frozen page with the server-side draft
locked, with and without the host's prerequisite check).

## Result, 2026-11-21, commit `9abdcec`, clean tree

Two vendors, 13 variants, four arms, 104 evaluation runs per route style.

| Route style | Arm | Scripted planner decisions | Cached steps | Certified rejoins | Wrong-field fills |
| --- | --- | ---: | ---: | ---: | ---: |
| slug (`/<case name>`) | `whole` / `suffix` | 93 / 93 | 35 / 35 | 0 / 0 | 0 / 0 |
| slug | `whole-rc` / `suffix-rc` | 59 / 59 | 59 / 59 | 0 / 0 | 0 / 0 |
| numeric (`/<integer>`) | `whole` / `suffix` | 93 / 93 | 35 / 35 | 0 / 0 | 0 / 0 |
| numeric | `whole-rc` / `suffix-rc` | 59 / 59 | 59 / 59 | 0 / 0 | 0 / 0 |

- Safe: every run met its expected behaviour, the 14 safe-stop rows per arm stopped,
  and the graph was unchanged after reuse.
- No gain: with the matcher on, every row is identical to exact matching. It certified
  no rejoin on `reordered`, `changed-label`, `extra-question` or `dependent-question`.
- Hidden state (numeric routes): the 16 checked rows dispatched nothing, and the 16
  negative controls dispatched 112 effects, 7 in every run. No matcher can see the
  locked draft; the host's step-authorization gate is what stops the write.

Why it certified nothing here, read from a temporary log line that is not committed:

- Slug routes: a profile is only considered when the page's normalized URL path equals
  the learned one. Integers, UUIDs and codes are normalized; slugs are not, and each case
  here has its own path.
- Numeric routes: all seven profiled nodes were rejected, five for
  `unsatisfied-live-slot-valuation` and two for `missing-footprint-locator`. The
  starting state has no profile (seven profiles for eight nodes), so a first page that
  differs from the learned one cannot be entered, and a page whose filled fields are not
  exactly a learned prefix cannot be rejoined.

## A second implementation, for comparison

Branch `workspace/suffix-eligibility` (commits `65503ca` to `cad7017`, based on
`e7c0279`, not on main) holds a different matcher, written the same day and run through
these same arms. Its write-up is `suffix-ablation.md` on that branch.

| Same 104 runs, slug routes | Decisions without resume | Decisions with resume | Certified rejoins | Wrong-field fills |
| --- | ---: | ---: | ---: | ---: |
| Matcher on main | 93 to 93 | 59 to 59 | 0 and 0 | 0 |
| Branch matcher | 93 to 64 | 59 to 29 | 23 and 30 | 0 |

With a real planner on the six completing variants, the branch matcher went from 42
to 12 model calls and 111.5 s to 39.0 s on one shared teaching run per vendor
(0.457 USD in total).

## What this does and does not show

- Each matcher did well on the evaluation built alongside it. This experiment was built
  before either, and only the branch matcher gains on it.
- The branch matcher has not been run on the sandbox families' 24 adversarial
  near-misses. Until it is, its safety is established only on this experiment's cases.
- A scripted function stands in for the planner in the controlled runs. One holdout per
  vendor, contact fields only, synthetic faults, and two vendors that behave almost alike.
- Zero wrong-field fills over 30 certified rejoins bounds the failure rate only below
  about 10% at 95% confidence.
