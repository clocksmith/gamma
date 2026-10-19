# Model-ranked recipe plus literal repair

On ten original consumed fit captures, the structural control answered 4/10
correctly, literal repair 6/10, and combined recipe/literal repair **7/10**.
Every arm had zero wrong acceptances and zero infrastructure failures. There
were no lost correct answers. All ten graphs were valid. The added correct
answer was lcd:1464; both literal gains (lcd:1046, lcd:1710) remained correct.

The opt-in route considers at most two highest non-current recipe logits per
active recipe slot and four globally ordered alternatives. It changes one
recipe operation while preserving edges, bindings, types and literals. Strict
typed validation rejects incompatible ports before execution. If no recipe
passes public examples, the original literal search gets the remaining budget.
Both stages share **four extra public executions and 0.25 seconds** per case.
No target graph, expected repair value or independent test selects an edit.
The default route remains unchanged.

The candidate used 17 extra public executions across ten cases, versus 20 for
literal-only. The inherited `literal_executions` field in the frozen driver and
summary means total repair executions for the combined arm, including one
recipe execution. All thirty public decisions were sealed before independent
source tests were opened. Run time was 4.388 seconds, under two CPU threads,
2 GiB and a 120-second wall cap.

This is consumed-fit correctness evidence with inference excluded, not new
end-to-end latency, protected generalization or release qualification. Official
two-second end-to-end acceptance and historical scores remain unchanged.
No training, protected opening, service intervention or source generation.

Software verification: 48 focused tests plus four subtests passed, covering
recipe ranking, strict ports, shared budget, capture mismatches, infrastructure
failure, accepted-control preservation, literal repair, judge and lane. Changed
Python compiled and the module imported during tests.

Evidence: [manifest](candidate.json), [summary](summary.json),
[decision seal](decisions-seal.json), [once-only driver](run_semantic.py).
Raw captures, decisions and independent score records stay local under
`runs/typed-semantic-fit-128-v1`. This candidate is separate from the preserved
[literal-only result](../typed-literal-semantic-fit-128-v1/README.md).

Remaining failures are lcd:2144, lcd:1101 and lcd:1489. The present bounded
proposal order does not solve them. Further development needs a separately
frozen construction hypothesis; no bounds were expanded after this score.
