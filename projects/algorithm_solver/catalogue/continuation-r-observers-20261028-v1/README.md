# R official observer/native profile v1

This is a separate prospective transport for the six available R members:
146,147,155,160,173,188. Reserved membership156,159,161,163 remains premium/public
specification blocked. Original R references/freeze, P profiles and source bytes
are unchanged. No candidate module was opened or executed while developing this
profile; tests use inert explicitly scoped toy classes/functions only.

Python calls original `Solution.insertionSortList`, `getIntersectionNode`,
`maxProfit`; JavaScript calls original named functions with those names. Neither
language falls back to solve or a different wrapper. Native class traces call
the original `LRUCache(capacity)`, `MinStack()`, `BSTIterator(root)` and original
declared methods on one fresh receiver per trace. Method descriptors are captured
before construction, class/prototype identity is checked afterward, and reuse of
a receiver across traces is rejected. Own class state may mutate. Void methods
must return actual None/undefined; numeric and Boolean methods remain distinct.

The source-defined node constructors are used directly:147 ListNode(val=0,next
null),160 ListNode(val) initializes next null,173 TreeNode(val=0,left/right null).
No class/constructor injection, source rewriting or algorithm helper substitution
is performed. Python nodes use exact own dictionary fields; JS nodes use exact
own data fields with unchanged property flags and source prototype. A variant
with a different layout requires a separately reviewed profile, never coercion.
`native_graphs.py/.cjs` are independently versioned generic guards, not edits to
prior transports. Their node envelopes are exact R representation bounds5000,
60000 and100000, not changes to sandbox limits.

147 wire `__list_node__` creates one native head. Every original physical node
must remain in the returned acyclic list, with its original value; ties may have
any order. The original argument head can end up inside the sorted output, so
its post-call suffix is observed separately. The host checks sortedness and IDs.
These observations do not establish insertion-sort algorithm compliance: the
explicit official algorithm requirement still needs independent source review.

160 wire `__list_graph__` creates one shared physical pool and projects exactly
two native head arguments. Public template pins bind the two-head interface;
the raw official API's five custom-judge fields are never passed to the program.
The observer preserves intentional cross-head aliases, checks unchanged topology
and records the actual returned original node ID or null. A value-equivalent
clone cannot pass. `node_identity` carries before/after rows(id,value,next), two
argument_roots and result_root; native alias relationships are authoritative in
that identity table. Root alias_edges refer to the two actual native arguments.

173 constructor receives the real source-defined TreeNode. Before/after physical
node tables verify the local frozen authored variant's nonmutating-tree contract.
That local contract is explicitly not a universal official requirement. Iterator
state belongs to the receiver; next/hasNext output and types are checked against
the independent reference.188 observes ordinary original arguments and the exact
integer result. `host_check.py` binds every uniform observation to the frozen R
reference, effects, primitive types, method snapshots and physical integrity.

## Prospective packets and retained full-size witnesses

`plan.py` pins the independent pre-source reference freeze and generates only
argument-bearing `gamma.r-official-packet.v1` packets; expected answers stay on the
host. Ordinary batches contain at most32 distinct calls plus their first repeat.
Large witnesses repeat if both envelopes fit, otherwise a small existing probe
brackets the original large call. Every excluded witness is retained explicitly
as blocked; there is no silent omission or cap increase. Main accepts at most33
calls, bounding retained receiver identities for source classes without weakref
support. Full class method traces remain intact in one call on one receiver.

The frozen plan covers all7,264 cases,242 batches and7,510 calls per language.
Four packets use small–large–small. No transport witness is blocked. Largest
host packet:2,977,950bytes; maximum conservative successful output:14,508,404bytes.
Both use16MiB envelopes. Child RLIMIT_FSIZE remains1MiB and is not a host-input
cap. The existing CPU3s/wall8s/memory1GiB/process16/FD64/stdout16MiB limits remain
unchanged. Input/output planning is not a hard aggregate memory bound and does
not establish actual candidate runtime/resource readiness.

Successful output projections include the entire physical graph, before/after
arguments, class output/type/snapshot vectors, newline/terminal overhead and
explicit147tie-pointer margins. The actual output monitor remains authoritative;
process failures and raw streams must be retained before host judging. A tested
100000-node toy produced12,711,868Python bytes and12,711,873JS bytes, below its
projection. No runtime freeze or sandbox run was created here.

## Validation and remaining gates

```sh
python3 -m unittest -q test_observers test_integration
node test_observers.cjs
```

25Python/source-free integration controls and18JS controls pass; every available
ID's toy observer record passes the frozen host semantic/effect checker. Syntax
and scoped Ruff pass. Full-node toy controls additionally verify iterative native
handling and output projection. Reference/source files are never imported as
candidate modules in these checks.

`native-bindings.json` pins code, public template evidence and the private
prospective packet-plan hash. It is an interface/profile record, not a new source
registry or approval. The exact12-source manifest and source-interface declarations are now
metadata-bound without opening candidate bodies. Actual gated source-byte
verification, independent observer and mandatory source review, Linux preflight/
runtime freeze, raw execution/replay and publication approval remain pending. Retain premium exclusions and all failures.
