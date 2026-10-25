# Deferred trace reconstruction, exact successor

This engine retains the v4 finite candidate worklist, source selection, admissible
bound, lexicographic objective, tie breaks, and full literal-byte charges. It
continues a separately reviewed accepted vocabulary prefix, never resets it.

The unchanged pinned trie kernel computes exact selection/character counts.
Rejected proposals do not construct Python token-string lists. Before generating
any current state's adjacent-composition worklist, every source trace is fully
materialized and both counts checked against the deferred representation. Every
accepted event still passes the independent two-segmenter/packet-decode cost check.
No omitted worklist candidates, changed budget, or semantic qualification reuse.

Activation requires randomized cache/materialization tests, all actual source
counts matching full tracing, and exact winner/source-choice/dictionary equality
on a recorded predecessor state. Kernel and transitive dependency pins remain.
Protected populations remain closed; development metrics are not M1 results.
