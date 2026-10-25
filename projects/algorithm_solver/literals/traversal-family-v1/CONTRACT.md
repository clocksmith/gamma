# Shared traversal family: additional same-language algorithms

Fixed development-fit IDs 103, 104, 107, 111, 112. These are additional JavaScript
source choices, not replacements for existing references or a new population.
Freeze their complete source bytes before any candidate execution or vocabulary
fitting. All five retain the original typed-tree input and result/effect contract.
Qualification uses the original independent oracle and complete historical
observations under the same pinned isolated runtime and resource limits.

Each full source contains an explicit iterative left-before-right DFS walker
that transports caller state and invokes a fully written callback. It returns no
task answer, mutates no input node, and uses O(h) pending traversal stack on a
binary tree. Every helper, callback, constant and invocation byte is charged.
There is no runtime code generation, answer lookup or implicit expansion.

- 103 replaces level-order queue traversal with DFS collection by depth followed
 by reversal of odd result levels. Left-before-right preorder preserves the
 left-to-right order within each depth on the admitted ordinary typed trees.
- 107 uses the same depth collection then reverses the result-level array.
- 104 replaces recursive depth aggregation with explicit traversal/max depth.
- 111 replaces recursive minimum depth with explicit leaf-depth aggregation;
 empty input stays 0 and a one-child node is not treated as a leaf.
- 112 transports the original remaining target along each root-to-leaf path.
 Leaf testing retains exact `node.val === remaining`, rather than subtracting
 and testing zero, to avoid changing Infinity/NaN/strict-equality edge behavior.
 Traversal may continue after finding a path, but preserves O(n) worst-case time,
 O(h) stack, output and absence of input mutation. Runtime caps remain unchanged.

The admitted tree transport hydrates ordinary data nodes, not arbitrary getters,
proxies or function-valued properties. No universal equivalence claim for such
external contexts is made. DFS/BFS read order changes require the frozen original
oracle/type/effect replay; source-level reasoning alone is not qualification.

The complete generic walk definition is NOT automatically eligible as a literal:
collecting a preorder traversal through a trivial callback could itself be a
whole benchmark algorithm. Keep its full definition/body excluded. Any gains
must come from multiple shared partial control-flow literals, with full expanded
bytes and callback/task logic still present. The existing eight audited
primitive allowlist does not implicitly expand to this helper.

Final 100/protected 66 remain closed. These five variants enter only a later linked
source-supply freeze after independent exact-byte qualification. No new fitting
arm or dictionary reset is authorized by this source-only contract.
