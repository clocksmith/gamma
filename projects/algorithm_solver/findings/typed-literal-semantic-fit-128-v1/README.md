# Bounded literal repair: consumed-fit correctness replay

On the ten original fit captures, structural control answered 4/10 correctly;
bounded literal repair answered 6/10 correctly, with zero wrong acceptances,
zero lost correct answers and zero infrastructure failures. The gains were
lcd:1046 and lcd:1710. All ten graphs were valid in both arms.

The route used only captured model margins, deterministic typed construction and
query-public examples. All twenty public decisions were sealed before the
original qualified independent source tests were read. Twenty extra public
executions were used across the ten cases; limits remained four per case and
0.25 seconds extra within a two-second local construction budget.

This is correctness evidence on consumed fit examples, not fresh inference or
release qualification. Capture replay excludes embedding/prediction time. Current
timings are contended; the official two-second end-to-end gate and historical
scores are unchanged. No protected case, training or serving-worker interruption.

Evidence: [summary](summary.json), [manifest](candidate.json),
[decision seal](decisions-seal.json), [driver](run_semantic.py).
Raw decisions, source and independent scoring remain local under
`runs/typed-literal-semantic-fit-128-v1`. Run once, completed in 3.232 seconds.
