# Cheap checks against the flow method, on unseen projects near 64 characters

Nine four-file projects that use 66 to 70 distinct characters, chosen by a seeded rule. For each: does it
fit a 64-entry dictionary once shared fragments are used, which method shows it, and at what cost?

- `PREREGISTRATION.md`: corpora, methods, limits and predictions, committed before any method was run.
- `RESULTS.md`: what happened.

## Check it

```sh
python3 -B evaluate.py --selftest      # the checker's own tests
python3 -B evaluate.py                 # recomputes the cheap checks, re-checks every certificate and dictionary; no solver
python3 -B run_benchmark.py            # reruns the measurements; needs scipy
python3 -B select_corpora.py --gamma PATH --fawn PATH --doppler PATH --reploid PATH    # rebuilds instances.json from the pins
shasum -a 256 -c SHA256SUMS
```

Entry rules, certificates and replay come from `capacity-complexity-v1/evaluate_real.py`. Prior work is
listed in `capacity-complexity-v1/README.md`.
