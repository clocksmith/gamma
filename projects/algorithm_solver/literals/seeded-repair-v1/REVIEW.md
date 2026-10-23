# Review and run receipt

Freeze/code/contract `83ea5f291` pushed before launch. Claude reviewed at
2026-10-23T21:27Z in shared Gamma LOG and approved: identical paired models/options,
fully checked incumbent, successful setSolution requirement, no hidden fallback,
balanced order, complete decoding, retained failures and research-local version
pin. No amendments or budget exceptions.

Launched2026-10-23T21:28:34Z with pinned SciPy Python/HiGHS, threads1 and
OMP/BLAS1/PYTHONHASHSEED0. Four pair workers cores12–15,8GiBaddress-space per
process,1200-second overall cap. Load13.84/12.51/10.31. Private run
`seeded-repair/run-v1`, log `seeded-repair-run-v1.log`. Eight snapshots from the
unchanged seed seal before any solver call;16calls each capped90solver seconds.
No validation source values or cases loaded. Together with24/25 this is10search
workers, under PLAN12-worker limit; Claude22cores26–31remain separate.

Four tests include32exhaustive comparisons with SciPy and both direct conditions,
invalid/optional starts and zero-time feasible-point retention. Compile/import/
help and code/runtime/input hash checks passed. Reporting rebuilds model/start
checks and packets without solving; README/evidence carry final outcomes.

Completed with exit0,374.93seconds wall time. All16calls timed out at90seconds
without a processed branch node; all feasible, none optimal or seed-improving.
Warm exact cost24750in all8pairs, cold28678–29786. All4800packets decode;
independent reporting rebuilds all8hashed models and feasible starts. W1/W2/W5/W6
hold; W3/W4fail. Complete warm/cold call sums727.91/726.37seconds.

Post-hoc attribution added after the first limited results: apply the existing
search's incumbent-retention rule to both returned points. Every pair then ties
at24750. This does not alter frozen predictions/tool recommendation; it prevents
claiming a search improvement from a better but nonimproving solver output.
