# Prelaunch amendment 1: occurrence construction and independent replay

2026-10-23, after freeze `1465cdaff`, before any item28 corpus run. Claude's
review approved the mathematical scope but found a feasibility issue: the
inherited builders construct and hash a fresh substring at every possible
length. Removing the length ceiling can make their character-copy work quadratic
in the maximum length per starting position. This amendment changes occurrence
enumeration only. The source population, pool, bans, seed union, capacity,
objective, optimizer updates, predictions, core0/core1 allocation and all budgets
remain as frozen. No corpus probe preceded this amendment.

`fraction-capacity-v1/dual.py` is byte-for-byte unchanged. `occurrence.py` provides
a subclass whose constructor traverses a dictionary prefix trie from each start,
stopping at the first absent prefix. It emits the same edges in sorted program,
start and end order, with identical optional occurrence IDs, entry IDs and costs.
It inherits the old floating shortest-path method and integer backward
certificate method unchanged. `run.py` binds this subclass into the inherited
optimizer instead of the substring-slicing constructor.

The independent verifier uses a separately implemented Aho-Corasick automaton
with failure links, output links and memoized sparse transitions. It never calls
the graph constructor or its prefix traversal. A first pass counts optional
matches at each start; prefix sums assign their offsets in the stored multiplier
vector. A second pass visits matches by increasing end, consuming each start's
multipliers in increasing end order. Every predecessor distance is already final,
so this is a forward DAG shortest path with Python integers. Mandatory matches
consume no multiplier. All entry sums and the top256 subtraction are exact.
Program boundaries reset the automaton and offsets; leftover/missing/negative
multipliers or incomplete coverage fail closed.

For total pattern bytes P, text bytes N, matches E, maximum pattern length L and
alphabet size A, the graph constructor takes O(P + N*L + E) time in the worst
case, with no substring copies or repeated substring hashing. It stores O(P+N+E)
items, including the original graph's occurrence-order receipt. The independent
verifier uses O(P*A + N + E + K log K) time, where K is the pool size; A is at
most96 for the frozen ASCII sources. Its storage is O(P*A + N + K), in addition
to the input multiplier vector. Sparse transition caching and output links avoid
copying every state's complete output list or materializing occurrence tuples.
These bounds do not remove the explicit pool's own potentially large output or
prove a run will fit the budget. The existing8GiB/worker and2400-second global
failure behavior remains authoritative; no pool truncation is introduced.

Four new synthetic tests compare150 randomized old/new graphs, exact occurrence
order, shortest paths and four integer certificates per case. They also compare
100 independently brute-forced match sets, long repeated prefixes through159
characters, mixed mandatory multi-character entries, arbitrary-size integer
penalties, Unicode/NUL data and fail-closed missing coverage/multiplier vectors.
The six pool tests and five unchanged dual tests also pass. No source/case corpus
was used. Compile/import/help and regenerated code identities precede launch.

Reporting binds the same adapter, independently reconstructs the full pool,
checks its exact order/hash, then uses the Aho-Corasick forward verifier and
replays every packet and cost. It also rechecks pinned item13 qualification
source hashes. Reporting performs no multiplier search. The amended contract
pins this document, adapter/tests and updated run/builder; it records the original
freeze commit and dual hash. Root review, push and Claude's amendment review are
required before launch. No result or claim is added by this amendment.
