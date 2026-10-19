# Fresh matched inference with static guard filtering

The new static-guard candidate returns **7/10 correct**, compared with **6/10**
for the preserved recipe/literal route, **5/10** for literal-only, **4/10** for
structural control and **6/10** for nearest training graph. Every arm has zero
wrong acceptances and infrastructure failures. There are no lost correct answers.
The filter adds lcd:2144 over its matched semantic control; gains over structural
control are lcd:1464, lcd:1046 and lcd:2144. All ten raw predictions exactly match
historical original-checkpoint captures. The original corpus, encoder and codec
hashes were checked before inference.

| Route | Correct /10 | Valid /10 | p95 seconds |
| --- | ---: | ---: | ---: |
| Raw | 4 | 8 | 3.021 |
| Structural control | 4 | 10 | 3.022 |
| Literal repair | 5 | 10 | 3.023 |
| Recipe plus literal | 6 | 10 | 3.024 |
| Static guard candidate | **7** | **10** | **3.023** |
| Nearest training graph | 6 | 10 | 3.018 |

The candidate still fails the unchanged two-second p95 end-to-end gate. No
latency, release or protected generalization qualification is claimed. The prior
fresh 5/10 semantic result remains intact; its current matched control is 6/10
because timing outcomes changed. Only the matched 6-to7 gain is attributed to
the new filter. No causal timing benefit from worker changes is claimed.

Capture-only replay is separately **8/10**, with two semantic failures:
lcd:1101 (three literal-bit errors) and lcd:1489 (seven). The current fresh run
loses lcd:1710 to the inference deadline before repair; this is different from
the prior run's timing losses. Semantic correctness is not relabeled as timing,
and timing abstentions are not counted as successful answers.

All sixty public decisions were sealed before original hash-bound independent
source tests were opened. Model-logit ranking, strict typed validation, four
extra public executions and 0.25 seconds total repair remain unchanged. The
candidate used six extra public executions across ten cases. Defaults remain
unchanged; the static filter is opt-in and never touches accepted controls.

The run completed in 60.018 seconds under four CPU threads and an 8-GiB cap;
peak aggregate RSS was 5.190 GB, monitored disk 1.338 GB, with no resource-limit
failure. CPU compute and the isolated sandbox probe passed. Cold setup and
independent scoring remain separate from warm route timing; embedding, retrieval,
prediction, construction and public verification all count toward the route.
The 0.8B/2B contributors remained running and 27B contributors stayed stopped.
There was no training, protected scoring, download or service intervention.

Evidence: [manifest](candidate.json), [summary](summary.json),
[capture seal](capture-seal.json), [decision seal](decisions-seal.json),
[sandbox probe](sandbox_probe.json), [setup](setup.json), [driver](run_fresh.py).
Raw artifacts remain local under `runs/typed-guard-fresh-fit-128-v1`.
Inherited `literal_seconds`/`literal_repair` summary labels denote total repair
for semantic/guard arms, including recipe and static-filter work.
