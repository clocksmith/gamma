# Item 42 auxiliary reporting note — 2026-10-23

This is an auxiliary diagnostic requested after the frozen production launch,
before reading its private results. It changes none of the 121 pinned execution
files, objectives, six q scales, predictions, bounds, budgets or acceptance rules.
The frozen active contract SHA256 is
`9a7e6f65d6f83fbe5727386824e0a13f863783cf70a406c365e1ccd1e2be8009`.

`quantile_diagnostics.py` may run only after the owner/root confirms that the main
independent replay is complete. Its caller must supply that accepted report's
SHA256. The script verifies the contract, all frozen code/runtime pins, parent
public evidence, complete production/replay supervisor receipts, the report's
production-result hash, cohort source/q hash metadata and each retained point
proof hash. It never opens source/q files, executes cases, reruns cardinality DP,
solves an assignment or optimizes. It rechecks the retained integer assignment
primal/dual or Hall proofs using the frozen pure checker. The main replay remains
the authority for the cardinality costs and full-substring pool certificate.

For each q scale, report all minimizing median-union values of `a`. Choose the
smallest minimizing `a`, and use its **retained** certified optimal assignment;
do not search alternative optimal assignments. For each assigned capped class
with cap `K`, find the minimum `k >= 1` with `d_p(k) == d_p(K)`. This is the
minimum edge count among paths attaining that capped optimum, because the
recorded `d_p(k)` minimizes over paths of at most `k` selections. The row is tight
exactly when that minimum equals `K`, equivalently
`d_p(K) < d_p(K-1)` with unavailable costs interpreted as positive infinity.
The arrays must be monotone, integer-valued where finite, and have no finite to
unavailable transition.

Publish per-class cap, minimum-edge histogram, assigned count and tight count.
The 15 uncapped programs have no cap-tightness statistic and are excluded from
the 285-program denominator. If the exact quantile family is certified empty,
report no selected `a`, histogram or tightness fraction. Also publish exact-minus-
necessary and necessary-minus-unrestricted **path numerator** differences over
the unchanged denominator. These are not differences of rounded integer bounds.

The chosen assignment and minimizing-`a` ties matter. These diagnostics do not
prove which constraint caused the bound, produce a capacity-feasible dictionary
witness, or establish M1 or a 400/500-program exclusion. Selections exclude Finish;
actions add one Finish per program. No source strings, q arrays, cost arrays,
program assignments or dual potentials appear in public auxiliary output.

Only three new files belong to this change: this note, the auxiliary script and
its focused test. Synthetic tests construct monotone cost arrays and exact dual
receipts directly, including unique/tied minima, plateaus, infeasible families
and corruptions. They do not run the production solver or cardinality DP.

Proposed later invocation, only after root supplies the accepted report hash:

```text
python -B quantile_diagnostics.py --run RUN --main-report MAIN_REPORT \
  --main-report-sha256 VERIFIED_SHA256 --output NEW_AUXILIARY_DIRECTORY --core 4
```

The auxiliary process has a separate 120-second wall guard, 8 GiB address-space
cap and one selected core (4 or 5). It cannot alter the production/main-report
directories. Failure withdraws any previous auxiliary result; the main report and
its certificate remain unchanged. No private receipt has been read to prepare
this note or the implementation.
