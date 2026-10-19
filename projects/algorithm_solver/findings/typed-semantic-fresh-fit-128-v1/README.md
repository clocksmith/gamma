# Fresh matched composition after the fleet-owned 27B stop

Using the recovered original checkpoint, corpus, codec and local encoder with
verified frozen hashes, all ten fresh raw predictions exactly matched historical
captures. No training, rebuilt assets or new downloads were used. The separate
fleet task had stopped both 27B contributors; the 0.8B and 2B workers remained
active. This was a shared-host run, not an exclusive-host timing claim.

| Route | Correct /10 | Wrong accepts | Abstentions | Valid /10 | p95 seconds |
| --- | ---: | ---: | ---: | ---: | ---: |
| Raw graph | 3 | 0 | 7 | 8 | 3.236 |
| Structural control | 3 | 0 | 7 | 9 | 3.239 |
| Literal repair | 4 | 0 | 6 | 9 | 3.241 |
| Recipe plus literal repair | **5** | **0** | **5** | **9** | **3.241** |
| Nearest training graph | 5 | 0 | 5 | 10 | 3.229 |

The combined candidate adds lcd:1464 and lcd:1710 over structural control, with
zero harmful corrections and zero infrastructure failures. Eight extra public
executions were used, versus eleven for literal repair. The original four-extra-
execution and 0.25-second shared repair limits remain inside the two-second
end-to-end gate. Cold setup and independent scoring are reported separately.
Fresh embedding, retrieval, prediction, construction and public checking all
count toward each applicable route. Controls and candidates share the measured
inference and structural prefix without omitting its cost.

The unchanged p95 requirement fails, so **no release or latency qualification**
is claimed. Correctness gains are real on these consumed fit cases; the frozen
`fit_development_signal` combines correctness and latency and is therefore false.
The separate [capture-only replay](../typed-semantic-fit-128-v1/README.md) remains
7/10 vs 6/10 vs 4/10 and cannot substitute for fresh inference performance.
No causal attribution of remaining timing variation is made.

All fifty route decisions were sealed before original independent source tests
were read. The candidate was frozen before this run and was not retuned after
scores. Protected targets remain unopened. Raw artifacts stay local under
`runs/typed-semantic-fresh-fit-128-v1`; metadata is preserved here.

Run: 56.599 seconds; four CPU threads; 5.218 GB peak aggregate RSS against an
8-GiB cap; 1.315 GB monitored disk; no resource-limit failure. CPU runtime and
sandbox probe passed. No worker intervention occurred in this execution task.
The source, weights, corpus, vocabulary and historical evidence hashes remained
unchanged during execution.

Evidence: [summary](summary.json), [manifest](candidate.json),
[capture seal](capture-seal.json), [decision seal](decisions-seal.json),
[sandbox probe](sandbox_probe.json), [setup](setup.json), [driver](run_fresh.py).
The frozen summary's inherited `literal_seconds` / `literal_repair` labels mean
total semantic repair for the combined arm, including recipe search.
