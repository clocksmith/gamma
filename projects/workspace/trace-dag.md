# State-reconvergent recipe DAG, graph compression and dynamic programming

`src/client/trace-dag.js` and `src/client/trace-graph-dp.js` implement Fawn's
opt-in recipe graph cache, reduction pass and backward Bellman dynamic
programming router above stock Chromium. The caller selects a task template,
supplies current input slots, authorizes intermediate clicks and explicitly
starts recording, composition or replay. Neither module can acquire browser
ownership or grant permission; `WorkspaceService` remains the sole effect and
admission owner.

`src/client/workflow-agent.js` composes this recipe graph with the bounded
planner loop (`learn`, `fresh` and `reuse` modes). Learning records the
planner's slot-bound actions and publishes atomically only after the caller's
independent review verifier accepts the actual rendered output. Reuse runs DP
replay first and hands structural misses or proven never-dispatched stale
actions to the planner. Authorization failures and uncertain effects stop the
run immediately without retries or renewed grants. Callers may opt into
`learnRepairs: true` to persist verified repairs and `reconvergeMidRepair: true`
to let an in-progress repair resume zero-call DP replay as soon as a planner
action lands back on a known DAG state.

```js
const limits = { maxNodes: 64, maxEdges: 64, maxSteps: 12 };
const dag = new TraceDag(limits);
const options = {
  service, owner, pageId: 'main', intent: 'form', template: 'review-form-v1',
  inputs: { name: currentProfile.name },
  intermediateClicks: [['button', 'Continue', 'button', '']],
};
const session = dag.session(options);
await session.record({
  kind: 'fill', locator: ['textbox', 'Full name', 'input', 'text'], slot: 'name',
});
// Record remaining approved intermediate steps, verify the pre-submit screen,
// then contract loops, reduce dominated detours and publish atomically.
await session.finish();
const result = await dag.session({ ...options, inputs: nextProfile }).replay();
```

## State identity and reconvergence (`version: 3`)

Earlier versions (`version: 1` and `version: 2`) hashed the entire ordered
action prefix into every node ID, turning the cache into an unmerged prefix tree
where alternative paths could never share suffixes or enter midway.

Version 3 (`new TraceDag(limits)`) replaces full ordered-prefix hashing with a
monotonic Markovian state key:

- **Unscoped exact-page nodes** hash
  `[scope, ['state-v3', outlineSlots, sameOutlineClicks], structuralOutlineHash]`,
  where `scope` binds `[template, origin, readScope, accountScope?]`.
  - `outlineSlots` is the **sorted set** of input slot hashes filled or selected
    while on the current structural outline. Commuting fills on the same screen
    (`fill A -> fill B` vs `fill B -> fill A`) converge to the same node
    `outlineSlots = [A, B]`.
  - Whenever an action transitions to a new structural outline
    (`nextOutline !== beforeOutline`), `outlineSlots` resets to `[]` and
    `sameOutlineClicks` resets to `0`. Any route, repair or sub-recipe arriving
    at that screen therefore maps to the **exact same node ID**.
  - When an intermediate `click` leaves `structuralOutlineHash` unchanged,
    `sameOutlineClicks` increments by `1`, preventing same-outline self-loops.
  - When a `goal` is supplied and a transition reaches a leaf review screen with
    zero remaining authorized controls (`elements.length === 0`), the state key
    uses `['state-v3-goal-leaf', goalHash]` so distinct goal review screens do
    not collide on the empty element outline while all non-empty interior and
    junction screens remain shared across goals.
- **Scoped field-group nodes** (`src/client/field-group-scope.js`) hash
  `[scope, ['scoped-v3', groupIndex, filledSlots], groupOutline]`, normalizing
  reviewed field aliases and unordered fills within each group so permutations
  reconverge at the group transition boundary.

Service ownership is still distinct from website account identity: callers must
supply `accountScope` and `verifyAccount` whenever multi-account reuse is
possible.

## Graph reduction and path compression (`src/client/trace-graph-dp.js`)

Every `publish()`, `TraceDag.merge()` and `TraceDag.compose()` pass runs two
deterministic reduction stages before validating limits:

1. **Intra-trace loop contraction (`compressTraceRecords`)**:
   - Given staged transitions $s_0 \to s_1 \to \dots \to s_m$, any state
     revisitation $s_i = s_j$ ($j > i$)—such as opening and closing a wrong
     drawer/modal or redundantly re-filling an already-settled slot on the same
     outline—is contracted in $O(m)$ to jump directly from $s_i$ to the suffix
     starting at $s_j$.
2. **Whole-DAG reduction (`reduceTraceGraph`)**:
   - **Topological acyclicity (`topologicalSort`)**: Kahn's algorithm validates
     that the combined step-edge (`+1` rank) and repair-bridge (`+0` rank) graph
     has zero cycles and longest path $\le \text{maxSteps}$. Unlike `v1`/`v2`,
     unequal-length paths (e.g. a 1-step shortcut and a 3-step path) can legally
     merge into the same node; `node.depth` records the canonical longest-prefix
     rank.
   - **Dead-branch pruning**: Reverse reachability from `terminal: true` nodes
     removes non-terminal dead ends.
   - **Dominated click-detour compression**: When node $u$ has multiple
     pure-click chains reaching the exact same target node $w$ with no
     intermediate slot writes or terminals, strictly higher-cost detour edges
     are pruned and any intermediate relay nodes whose in-degree drops to `0`
     are garbage-collected.
   - **Join-semilattice normal form**: Edges are deduplicated (taking
     `Math.min` over optional positive `weight`s), nodes are ordered by
     `(depth, id)`, and re-publishing an identical trace is byte-for-byte
     idempotent.

`dag.compressionStats()` (`analyzeTraceGraph`) reports `nodeCount`, `edgeCount`,
`repairBridgeCount`, `terminalCount`, `sharedMergeNodes`, `confluentDiamonds`,
`maxDepth` and `optimalRootCosts`.

## Backward dynamic programming (`solveRecipeDp`)

Instead of aborting whenever a node has more than one outgoing edge, `replay()`
and `dag.solve({ inputs })` run a reverse-topological Bellman pass over the DAG:

- **Terminal base case**: Verified review boundaries (`node.terminal === true`)
  have $V(t) = 0$ and reachable terminal postcondition set $\Sigma(t) = \{t\}$
  when no `goal` is specified. When a session or `dag.solve({ inputs, goal })`
  passes a `goal` identifier, goal-specific completion mappings live separately
  from shared `nodes` in top-level `goalTerminals: [[goalHash, [nodeId, ...]]]`.
  For a known goal, only nodes in `goalTerminals[goalHash]` receive $V(t) = 0$
  while earlier goal terminals act as ordinary intermediate stops; for an unseen
  goal, slot-feasible prefixes advance up to the first known checkpoint and hand
  off cleanly to the planner.
- **Action Bellman backup**: Outgoing edges at node $u$ are grouped by canonical
  action $a = (\text{kind}, \text{locator}, \text{slot})$ with observed outcomes
  $O(u, a)$:
  - Actions whose `slot` is absent from the session's supplied `inputs` are
    marked slot-infeasible for the current run.
  - For feasible actions with at least one terminal-reaching outcome:
    $$Q(u, a) = \bar{w}(u, a) + \frac{1}{|O(u, a)|} \sum_{e \in O(u, a)}
    \begin{cases} V(e.\text{next}) & \text{if } V(e.\text{next}) < \infty \\
    C_{\text{replan}} & \text{otherwise} \end{cases}$$
    where $\bar{w}(u, a)$ defaults to `1` step (or the edge's explicit positive
    `weight`) and $C_{\text{replan}} = 1000$ penalizes branches with historical
    misses.
  - $V(u) = \min_a Q(u, a)$, propagated upstream across both step edges and
    `repairs` bridges.
- **Confluent tie-breaking vs semantic ambiguity**:
  - When a single action achieves $V(u)$, `replay()` dispatches it (selecting
    shorter paths over longer paths, lower-weight edges over higher-weight
    edges, reliable branches over flaky branches, and feasible-slot branches
    over missing-slot branches).
  - When multiple actions tie for $V(u)$ **and** reach the exact same terminal
    postcondition set $\Sigma(u, a_1) = \Sigma(u, a_2)$ (such as commuting fills
    forming a confluent diamond), `solveRecipeDp` breaks the symmetry
    deterministically by canonical step key.
  - When multiple actions tie for $V(u)$ and lead to **distinct** terminal
    states ($\Sigma(u, a_1) \neq \Sigma(u, a_2)$), `replay()` stops
    conservatively with `'ambiguous-branch'`.

## Recipe composition and mid-recipe entry

- **Modular composition (`TraceDag.compose` / `TraceDag.composeAll`)**:
  - Independently recorded `v3` sub-recipes sharing a namespace key (for
    example, `open-drawer`, `search-catalog` and `select-export-format`) can be
    stitched with `TraceDag.compose(first, second, limits)` or
    `TraceDag.composeAll([g1, g2, g3], limits)`.
  - Any node marked `terminal: true` in an earlier stage that has non-terminal
    outgoing continuation edges in a later stage becomes an interior handoff
    node (`terminal: false`), followed by `reduceTraceGraph`.
- **Mid-screen and pre-filled mid-form entry**:
  - Because screen transitions reset `outlineSlots` to `[]`, starting `replay()`
    when the browser is already on stage $k$ immediately matches stage $k$'s
    node and executes only the remaining suffix.
  - On step `0` of an unscoped `v3` session, if some fields on the current page
    already hold the exact supplied `inputs` values and match a strictly closer
    node ($V(\text{prefilled}) < V(\text{empty})$), `replay()` enters at that
    pre-filled state without re-entering settled fields.
- **Verified repair suffixes**:
  - `session.repair()` retains the executed prefix and bridges a scoped group
    miss to an exact-page node (`repairs: [exactNodeHash]`), carrying already
    satisfied group slots forward until the next screen transition.
  - With `reconvergeMidRepair: true` in `runWorkflow`, if a planner repair step
    transitions onto a node already present in `dag`, `session.continueReplay()`
    completes the known suffix from cache before running `verifyReview`.

Only `fill`, `select` and explicitly allowlisted intermediate `click` steps are
admitted. Native submit, image, file, password and hidden controls remain
excluded, and every step still binds a fresh `observationVersion`, unique
structural target, live handle/digest and disclosure check.

## Snapshot format and compatibility

`dag.export()` emits version-3 state by default:
`{version: 3, key, limits, nodes: [[nodeHash, {depth, edges, repairs, terminal}]], goalTerminals?}`
(`goalTerminals` is omitted unless goal-scoped sessions were published).
Each edge is `{next, step}` or `{next, step, weight}` where `step` is
`{kind, locator, slot}` (`slot` is `null` for clicks). Raw labels, input values,
URLs, selectors, handles and credentials are never stored in the graph. The
export remains sensitive private state and must stay in `0600` private storage
or sealed `WorkflowSync` envelopes.

`TraceDag.restore(state, limits)` accepts `version` `1`, `2` and `3`:
- Version `1` and `2` snapshots keep their ordered-prefix node fingerprints and
  strict `depth + 1` edge invariant.
- Version `3` snapshots enforce topological acyclicity, `maxSteps` rank bounds,
  repair boundary invariants and optional positive edge weights.

## Focused checks

```sh
node browser/workspace/test/unit/trace-dag.test.js
node browser/workspace/test/unit/trace-graph-dp.test.js
node browser/workspace/test/unit/scoped-trace.test.js
node browser/workspace/test/unit/workflow-repair.test.js
node browser/workspace/test/unit/workflow-completion.test.js
node browser/workspace/test/unit/workflow-store.test.js
node browser/workspace/test/browser/trace-dag.test.js
node browser/workspace/test/browser/workflow-repair.test.js
```
